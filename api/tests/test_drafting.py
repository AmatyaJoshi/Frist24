"""Drafting guard rails with a fake LLM (no Ollama needed) + a live Ollama test when reachable."""
import json

import pytest
from sqlalchemy import select

from app.models import Incident, Product
from app.schemas.reports import FACT_FIELDS, STAGE_MODELS
from app.services import drafting, llm
from app.services.facts import build_facts


@pytest.fixture()
def incident(db_url, db):
    inc = db.execute(select(Incident).join(Product).where(Product.sku == "HMI-4100")).scalars().first()
    if inc is None:
        pytest.skip("demo incident missing (run test_sync_live first)")
    return inc


def test_prompt_renders_all_placeholders(incident, db):
    for stage in ("early_warning", "notification"):
        for lang in ("en", "de"):
            bundle = build_facts(db, incident, lang)
            prompt, version = drafting.render_prompt(stage, bundle, lang)
            assert "{{" not in prompt, "unrendered placeholder"
            assert version in ("ew-v1", "nt-v1")
            assert incident.cve_id in prompt
            for k in STAGE_MODELS[stage].model_fields:
                assert k in prompt


def test_llm_output_facts_are_restamped_and_validated(incident, db, monkeypatch):
    bundle = build_facts(db, incident, "en")

    def fake_generate(prompt, model, **kw):
        keys = list(STAGE_MODELS["early_warning"].model_fields)
        out = {k: f"model text for {k}" for k in keys}
        out["vulnerability_id"] = "CVE-1999-9999"  # model tries to change a FACT
        out["actively_exploited"] = False  # and another
        out["initial_assessment"] = "Component X is used for Y. Impact Z. Unknown W."
        return out, {"model": model, "seconds": 0.1, "eval_count": 10, "prompt_eval_count": 100, "done_reason": "stop"}

    monkeypatch.setattr(llm, "pick_model", lambda: "fake:1b")
    monkeypatch.setattr(llm, "generate_json", fake_generate)
    rep = drafting.draft(db, incident, "early_warning", "en", actor="pytest")
    db.flush()
    assert rep.source == "llm" and rep.status == "pending_review" and rep.model == "fake:1b" and rep.prompt_version == "ew-v1"
    assert rep.content["vulnerability_id"] == incident.cve_id  # restamped from DB
    assert rep.content["actively_exploited"] is True
    assert rep.content["initial_assessment"].startswith("Component X")
    for k in FACT_FIELDS["early_warning"]:
        if k in bundle["facts"]:
            assert rep.content[k] == bundle["facts"][k]
    db.rollback()


def test_bad_json_then_good_json_uses_retry(incident, db, monkeypatch):
    calls = {"n": 0}

    def flaky(prompt, model, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise llm.LlmBadOutput("not json")
        assert "PREVIOUS ANSWER WAS REJECTED" in prompt
        keys = list(STAGE_MODELS["notification"].model_fields)
        return {k: "t" for k in keys}, {"model": model, "seconds": 0.1, "eval_count": 1, "prompt_eval_count": 1, "done_reason": "stop"}

    monkeypatch.setattr(llm, "pick_model", lambda: "fake:1b")
    monkeypatch.setattr(llm, "generate_json", flaky)
    rep = drafting.draft(db, incident, "notification", "de", actor="pytest")
    assert rep.source == "llm" and calls["n"] == 2
    assert rep.content["cvss_score"] == build_facts(db, incident, "de")["facts"]["cvss_score"]
    db.rollback()


def test_unavailable_llm_falls_back_to_template(incident, db, monkeypatch):
    def down():
        raise llm.LlmUnavailable("no ollama")

    monkeypatch.setattr(llm, "pick_model", down)
    rep = drafting.draft(db, incident, "early_warning", "de", actor="pytest")
    assert rep.source == "template" and rep.status == "pending_review" and rep.model is None
    assert rep.content["member_states_affected"].startswith("EU-weit")
    STAGE_MODELS["early_warning"].model_validate(rep.content)
    db.rollback()


def test_live_ollama_drafts_en_and_de(incident, db):
    try:
        model = llm.pick_model()
    except llm.LlmUnavailable as e:
        pytest.skip(f"ollama not available: {e}")
    for lang in ("en", "de"):
        rep = drafting.draft(db, incident, "early_warning", lang, actor="pytest-live")
        assert rep.source == "llm", f"expected LLM draft, got {rep.source}"
        STAGE_MODELS["early_warning"].model_validate(rep.content)
        assert rep.content["vulnerability_id"] == incident.cve_id
        assert len(rep.content["initial_assessment"]) > 40
        print(f"\n[{model} {lang}] initial_assessment: {rep.content['initial_assessment']}")
    db.rollback()
