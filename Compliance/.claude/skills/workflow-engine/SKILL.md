---
name: workflow-engine
description: ANUPAL workflow & approval engine contract — templates, approval matrix, pure transitions, SoD, OTP step-up, delegation, SLA/escalation, instance states, document and CAPA workflows. Use for contexts/workflow, inbox, reminders and any feature that needs approval.
---

# Workflow engine

Spec of states/templates: `docs/WORKFLOWS.md`. This is the code contract.

## Shapes
```python
class StepDef(BaseModel):
    key: str; role: str; unit_scoped: bool = True; sla_hours: int = 48
    min_approvers: int = 1; requires_otp: bool = False; can_delegate: bool = True
    actions: set[Literal["approve", "return", "reassign", "request_info", "comment"]]

class TemplateDef(BaseModel):
    key: str; subject: Literal["instance", "document", "override", "capa", "contractor_month", "event"]
    steps: list[StepDef]

def transition(run: RunState, action: Action, actor: Actor, now: datetime) -> tuple[RunState, list[Event]]:
    """Pure. Raises WorkflowError(code) for: NOT_ASSIGNED, SOD_VIOLATION, OTP_REQUIRED,
    REASON_REQUIRED, INVALID_ACTION, RUN_CLOSED."""
```
`service.act(ctx, run_id, action)` = load → `transition` → persist run + StepAction + AuditLog +
outbox events in ONE transaction. Nothing else may change run/instance state.

## Rules
- **Snapshot**: `WorkflowRun.template_snapshot` is copied at start (ADR-009).
- **Matrix**: ordered rules → template key (+ optional role overrides); `preview(ctx)` returns
  obligation → template mapping for the admin screen.
- **SoD**: a user may act in only one step of a run; approver ≠ anyone who uploaded/edited
  evidence or the document version being approved; requester ≠ override approver.
  `small_team_mode` (tenant flag, ≤ 5 users) downgrades SoD errors to recorded warnings.
- **OTP**: steps with `requires_otp` need a step-up token (≤ 5 min old) from identity.
- **Delegation**: resolve assignees through active delegations; record `on_behalf_of`.
- **Return** always needs a reason; it moves the run to the previous human step (or maker) and
  keeps the thread.
- **SLA**: on entering a step, schedule `sla_due` job; breach → `StepBreached` event → notify +
  escalate per ladder (T+1 checker/approver, T+3 compliance_head, T+7 owner).
- **AI**: runs whose subject has `ai_generated=true` can never skip the reviewer step; the matrix
  rule for AI is evaluated first and is not editable by tenants.
- Instance state machine (WORKFLOWS §1) is driven by run events: run completed → APPROVED; file
  action → FILED (delay reason if late); evidence complete → CLOSED.

## Tests
Table-driven paths for every default template incl. return loops, delegation, SoD, OTP, SLA
breach with fake clock, template edit during an in-flight run.
