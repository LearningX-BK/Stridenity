---
name: explainability
description: The AIAction contract — how every AI or rule-based result in ANUPAL records evidence, rationale, confidence and human verdict, and how the UI shows "Why". Use for any AI service, AI endpoint or AI UI card.
---

# Explainability contract

## Backend: every AI service follows this shape
```python
async def draft(instance_id, template, override, ctx) -> DraftResponse:
    async with record_action(ctx, capability=f"draft.{template}", entity=("instance", instance_id)) as act:
        det = drafting.deterministic(instance, template)  # sections from facts + fed data + rules
        ev = evidence.for_instance(instance, k=8)         # obligation cite, prior approved docs, inputs
        act.add_evidence(ev); act.add_rule_trace(det.trace)
        llm = await gateway.run(..., variables={..., "evidence": ev, "deterministic": det})
        out = merge(det, llm)                            # LLM may override; disagreement noted
        act.set_output(out, rationale=llm.data.rationale if llm else det.rationale,
                       llm=llm)                         # provider/model/prompt/usage
        act.confidence = confidence.compute(model_conf=..., evidence=ev,
                                            agreement=agree(det, llm), repaired=llm.repaired)
    return DraftResponse(result=out, action=act.summary())   # result becomes a DRAFT Document
```
- `record_action` persists even on exception (status `failed`, error message) and on degraded
  fallback (status `degraded`, mode `deterministic`).
- `mode`: `deterministic` (no LLM), `llm`, `hybrid`. Label honestly.
- `Evidence.why` is human text derived from score components, e.g.
  "POSH Rules r.14 requires the annual report; 3 complaints recorded in register (Jan–Dec 2026)".
- `Rationale.factors`: ≤ 5 items `{label, direction:+/-, weight 0..1, detail}`. User-facing,
  plain English. No chain-of-thought, no "As an AI".
- Confidence bands: high ≥ 0.75, medium ≥ 0.5, else low. `confidence_factors` explains the number
  (e.g. "+ all 6 required inputs fed", "− 2 complaints missing disposal date").
- Store `input_summary` (redacted, ≤ 2k chars) — never raw secrets or unredacted text.
- Human verdict: `POST /api/v1/actions/{id}/feedback {verdict, edited_output?, reason?}`; edits
  store a JSON diff. Accepted/edited outputs may feed few-shot examples (tenant opt-in, never across tenants).

## API
AI endpoints return `{"result": ..., "action": AIActionSummary}` where summary has
`id, mode, provider, model, confidence, confidence_band, status, latency_ms, cost_usd,
evidence_count`. Full detail via `GET /api/v1/actions/{id}`.

## UI
- Every AI card: title, result, `ConfidenceChip` (band + tooltip with factors), source label
  (`AI · claude-…` / `Rule` / `Hybrid`), actions: Accept · Edit · Reject · Re-run with… · **Why?**
- **WhyDrawer** (right side): Summary → Factors (± bars) → Evidence list (type icon, title,
  score bar, why text, link to obligation/document/evidence) → Rule trace → Model & prompt (provider, model,
  prompt id@version, tokens, cost, latency, redactions count by type) → Verdict history.
- Degraded results show a subtle banner: "Model unavailable — showing rule-based result".
- Never show a spinner without context: say what the AI is doing ("Reading your CTO conditions…",
  "Drafting with claude-…").

## ANUPAL specifics
- AI drafts are `Document`s in status DRAFT with `ai_action_id`; only the document workflow can
  approve them, and approval records the human verdict on the AIAction (accepted/edited).
- Extraction results (licence conditions, challan fields) are *proposals*; each accept/edit/reject
  is a verdict.
- The violet `AIChip` stays on content until a human approves it.
