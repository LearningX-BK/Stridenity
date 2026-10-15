---
name: tenancy
description: ANUPAL multi-tenant SaaS contract — TenantContext, isolation tiers (pooled+RLS, schema, dedicated), repository base, jobs, storage, encryption, control plane and break-glass. Use for any code that stores, reads, queues, caches, searches or exports tenant data, and for /ops features.
---

# Tenancy contract (ADR-007, ADR-017)

## TenantContext — always present
```python
@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID; slug: str; tier: Literal["pooled", "schema", "dedicated"]
    db_route: str            # engine key or schema name
    region: str; plan: str; flags: frozenset[str]; kms_key_ref: str
    actor_id: UUID | None    # user or ops user (break-glass)
    break_glass_session: UUID | None = None
```
- Resolved by middleware (`contexts/tenancy/middleware.py`) from subdomain / token claim
  (`X-Tenant` header only when `ANUPAL_ENV=dev`). Routes get it via `Depends(tenant_ctx)`.
  No context → 401/400. Never take tenant_id from request bodies.
- Jobs: `enqueue(ctx, kind, payload)` stores `tenant_id`; the worker rebuilds the context before
  running the handler. Cron jobs iterate tenants explicitly.

## Data access
```python
class TenantRepository(Generic[M]):
    def __init__(self, session: Session, ctx: TenantContext): ...
    def q(self) -> Select: return select(self.model).where(self.model.tenant_id == self.ctx.tenant_id)
    def add(self, obj: M) -> M: obj.tenant_id = self.ctx.tenant_id; ...
    def get(self, id) -> M | None   # filtered; returns None for other tenants' ids (no 403 leak)
```
- `session_for(ctx)` routes to the right engine/schema; on Postgres every transaction runs
  `SET LOCAL app.tenant_id = :id` so **RLS** (`USING (tenant_id = current_setting(...)::uuid)`)
  is the second wall. App role has no BYPASSRLS; migrations use the owner role.
- Unique constraints include `tenant_id`. Foreign keys never cross tenants (composite FK where cheap).
- Raw SQL only in `db/dialect.py` and must include the tenant predicate.

## Files, caches, search
Object keys `tenants/<tenant_id>/...` (pooled) or tenant bucket (dedicated). Envelope encryption:
per-tenant data key (Fernet) wrapped by the master/KMS key (`core/crypto.py`). Cache keys and
vector indexes are namespaced by tenant. Exports/reports run with the tenant's context only.

## Isolation tests (mandatory)
Every repository, router list/get, file download, search and job handler gets a case in
`backend/tests/isolation/` using the `two_tenants` fixture: create in A, read/update/delete as B
→ nothing visible, 404 on direct id. CI runs this suite on SQLite and Postgres (RLS on).

## Control plane (`contexts/tenancy/`)
Registry (tenants, tiers, routes, plans, entitlements, flags, meters, pack pins), provisioning
jobs (create schema/DB, run migrations, seed packs, invite admin), suspend/offboard (export →
crypto-shred data key), entitlement checks (`require_entitlement(ctx, "units", n)`), usage meters
(users, units, AI tokens, storage) incremented by domain events.

## Ops & break-glass
Ops users (`ops_admin`, `ops_support`, `ops_content`) authenticate separately (MFA mandatory) and
have **no** tenant context by default. Support access = `BreakGlassSession{tenant, ops_user,
reason, ticket_ref, approved_by (tenant admin) | emergency, expires_at (≤ 4h)}`; while active, the
ops user gets a read-only TenantContext with `break_glass_session` set and every request is
written to the tenant's AuditLog (visible to tenant admins). Expired → 403.
