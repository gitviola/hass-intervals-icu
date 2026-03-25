# Research: Wellness Data Write Support

## Decision 1: Use one generic write action for wellness updates

- Decision: Implement a primary service/action that accepts optional `date` plus a constrained set of writable wellness fields.
- Rationale: Single service keeps automation UX simple and avoids duplicated validation/logic for each metric.
- Alternatives considered:
  - Multiple metric-specific services (`set_weight`, `set_nutrition`): clearer per-call intent but duplicates validation and mapping logic.

## Decision 2: Default date to Home Assistant local date

- Decision: When `date` is omitted, compute target date from HA local time (`YYYY-MM-DD`).
- Rationale: Matches user expectation for "today" in HA automations and dashboards.
- Alternatives considered:
  - UTC date default: can mismatch user-local day near midnight.

## Decision 3: Enforce partial-update semantics via payload minimization

- Decision: Build outbound JSON with only explicitly provided service fields.
- Rationale: Intervals.icu wellness PUT endpoints support partial updates; this guarantees omitted fields remain unchanged.
- Alternatives considered:
  - Read-modify-write of full record: unnecessary extra request and race window.

## Decision 4: Use `/wellness/{date}` endpoint for deterministic target day

- Decision: Call `PUT /api/v1/athlete/{id}/wellness/{date}`.
- Rationale: Explicit path date improves clarity and aligns with service schema.
- Alternatives considered:
  - `PUT /wellness` with `id` in body: works but less explicit in integration flow.

## Decision 5: Refresh coordinator after successful write

- Decision: Trigger `coordinator.async_request_refresh()` after successful update.
- Rationale: Keeps sensor state aligned without manual reload.
- Alternatives considered:
  - No refresh (wait for next poll): stale UX.
