"""LLM drafting with deterministic guard rails.

    facts  = build_facts()                      # deterministic
    prompt = render(prompts/<stage>.md, facts)  # prompt_version from the file header
    out    = ollama(prompt, json mode)          # local model, temperature 0
    out[FACT] = facts[FACT]                     # FACTs are re-stamped from the DB, whatever the model wrote
    validate(out) or retry once with the validation error, else template fallback
    store as Report(status=pending_review, source=llm|template, model, prompt_version)

The model never decides anything: it fills TEXT fields, the human reviews.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import Incident, Report
from app.schemas.reports import FACT_FIELDS, STAGE_MODELS, UNKNOWN, text_fields
from app.services import llm
from app.services.facts import build_facts
from app.services.reports import create_report, template_content

log = logging.getLogger("frist24.drafting")

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
PROMPT_FILES = {"early_warning": "early_warning.md", "notification": "notification.md", "final_report": "notification.md"}
LANGUAGE_NAME = {"en": "English", "de": "German (formal register, 'Sie'; use the terminology anchors: aktiv ausgenutzte Schwachstelle, Frühwarnung, Meldung, Hersteller, Produkt mit digitalen Elementen, Abhilfemaßnahmen, zuständiges CSIRT (Deutschland: BSI))"}


def load_prompt(stage: str) -> tuple[str, str]:
    text = (PROMPTS_DIR / PROMPT_FILES[stage]).read_text(encoding="utf-8")
    m = re.search(r"^#\s*prompt_version:\s*(\S+)", text, re.M)
    version = m.group(1) if m else "unknown"
    return text, version


def render_prompt(stage: str, bundle: dict, language: str) -> tuple[str, str]:
    text, version = load_prompt(stage)
    facts = dict(bundle["facts"])
    facts["report_type"] = stage
    facts["member_states_affected_default"] = bundle["defaults"]["member_states_affected"]
    keys = list(STAGE_MODELS[stage].model_fields)
    fact_keys = FACT_FIELDS[stage]
    marked = {k: ("FACT" if k in fact_keys else "TEXT") for k in keys}
    facts_view = {"FIELD_KINDS": marked, "FACTS": {k: v for k, v in facts.items() if k in fact_keys or k == "member_states_affected_default"}}
    prompt = (
        text.replace("{{language_name}}", LANGUAGE_NAME.get(language, language))
        .replace("{{schema_keys}}", ", ".join(keys))
        .replace("{{unknown_phrase}}", UNKNOWN.get(language, UNKNOWN["en"]))
        .replace("{{facts_json}}", json.dumps(facts_view, ensure_ascii=False, indent=1, default=str))
        .replace("{{context_json}}", json.dumps(bundle["context"], ensure_ascii=False, indent=1, default=str))
    )
    if "{{context_json}}" not in text:  # early_warning.md has no CONTEXT slot; append it
        prompt = prompt.replace("FIELD GUIDE", "CONTEXT (background only; never copy into FACT fields)\n" + json.dumps(bundle["context"], ensure_ascii=False, indent=1, default=str) + "\n\nFIELD GUIDE", 1)
    return prompt, version


def _restamp_facts(stage: str, out: dict, facts: dict) -> tuple[dict, list[str]]:
    """Copy FACT fields from the DB over whatever the model produced. Returns (content, deviations)."""
    deviations = []
    content = {k: out.get(k) for k in STAGE_MODELS[stage].model_fields}
    content["report_type"] = stage
    for k in FACT_FIELDS[stage]:
        if k == "report_type" or k not in facts:
            continue
        if out.get(k) != facts[k]:
            deviations.append(k)
        content[k] = facts[k]
    unknown = UNKNOWN["en"]
    for k in text_fields(stage):
        v = content.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            content[k] = unknown
        elif not isinstance(v, str):
            content[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
    if stage == "final_report" and not content.get("fix_release_identifier"):
        content["fix_release_identifier"] = unknown
    return content, deviations


def _validate(stage: str, content: dict) -> dict:
    return STAGE_MODELS[stage].model_validate(content).model_dump()


def draft(db: Session, inc: Incident, stage: str, language: str, actor: str) -> Report:
    bundle = build_facts(db, inc, language)
    facts = bundle["facts"]
    prompt, prompt_version = render_prompt(stage, bundle, language)
    attempts: list[dict] = []
    try:
        model = llm.pick_model()
        current = prompt
        for attempt in (1, 2):
            try:
                out, meta = llm.generate_json(current, model)
                content, deviations = _restamp_facts(stage, out, facts)
                content = _validate(stage, content)
                rep = create_report(
                    db, inc, stage, language, content, source="llm", actor=actor, model=meta["model"], prompt_version=prompt_version,
                    extra_audit={"attempt": attempt, "llm_seconds": meta["seconds"], "eval_count": meta["eval_count"], "llm_fact_deviations_restamped": deviations, "attempts": attempts},
                )
                log.info("LLM draft ok: %s %s %s v%d (%ss, attempt %d, %d fact deviations restamped)", inc.cve_id, stage, language, rep.version, meta["seconds"], attempt, len(deviations))
                return rep
            except (llm.LlmBadOutput, ValidationError) as e:
                err = str(e)[:800]
                attempts.append({"attempt": attempt, "error": err})
                log.warning("LLM attempt %d invalid: %s", attempt, err[:200])
                current = prompt + f"\n\nYOUR PREVIOUS ANSWER WAS REJECTED: {err}\nReturn a corrected JSON object with exactly the required keys."
    except llm.LlmUnavailable as e:
        attempts.append({"error": f"unavailable: {e}"})
        log.warning("LLM unavailable, using template: %s", e)

    content = template_content(stage, bundle, language)
    rep = create_report(db, inc, stage, language, content, source="template", actor=actor, model=None, prompt_version=prompt_version, extra_audit={"fallback_reason": attempts})
    log.info("template fallback draft: %s %s %s v%d", inc.cve_id, stage, language, rep.version)
    return rep
