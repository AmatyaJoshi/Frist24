# TODO.md — cut or deferred scope (feeds the README "Limitations" section)

- [ ] Production `next build` for the web container (currently `next dev`).
- [ ] `docs/SPEC.md` missing from the delivered brief — confirm with owner or keep derived model.
- [ ] EUVD (ENISA EU Vulnerability Database) as EU-native second exploitation source — stretch.
- [ ] NVD enrichment (CVSS) — optional; OSV severity preferred.
- [ ] Kubernetes manifests (kustomize) as optional deployment target for the Devpost "deployment" bonus. Not required by the brief; compose is the contract. Only after feature freeze.
- [ ] German drafts from llama3.1:8b are usable but not native-quality ("Das betroffene Komponenten"); a larger or German-tuned model, or an EN→DE pass, would improve register. Human review covers it for now.
- [ ] CPU-only inference takes ~2 min per draft (14-core laptop, no GPU). Fine for the demo video with a spinner; GPU or a smaller quant for live demos.
- [ ] Review UI click-through (draft → edit → approve) verified via the API and type-checked; not yet exercised in a real browser on this machine (no browser automation available). Do a manual pass on a teammate's machine.
- [ ] Final report prompt: currently reuses notification.md.
- [ ] Observed hallucination in a TEXT field: llama3.1:8b described CVE-2020-11023 (XSS) as "potential for remote code execution" in `severity_assessment`. FACTs were intact. Reviewer must catch this; consider a post-check that flags severity words not present in the CVE text.
- [ ] History seed (`services/history.py`) written without a database on this machine; verify on the Docker laptop: `docker compose exec api python -m app.cli demo` should log "demo history staged for 5 incident(s)" and /incidents should show closed 2022–2023 incidents plus the two live ones.
