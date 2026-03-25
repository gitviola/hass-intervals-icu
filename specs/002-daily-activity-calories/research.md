# Research: Daily Activity Calories Sensor

## Decision 1: Keep summary calories unchanged and add a separate day-level metric

- Decision: Preserve existing summary calories as-is and introduce a new distinct
  daily activity calories metric.
- Rationale: Existing users may already depend on summary calories semantics, while
  the bug report requires a day-scoped value for dashboards/automations.
- Alternatives considered:
  - Replace existing summary calories semantics with day-level behavior: rejected
    because it is a silent behavior change and risks breaking existing automations.

## Decision 2: Anchor day-level calculation to Home Assistant local day

- Decision: Compute "today" using Home Assistant local calendar day for each refresh.
- Rationale: HA users expect date-scoped sensors to align with their configured local
  timezone and daily automations.
- Alternatives considered:
  - Anchor to summary row date: rejected because summary rows can represent weekly
    ranges.
  - Anchor to most recent wellness record date: rejected because wellness recency can
    diverge from activity recency.

## Decision 3: Source day-level calories from per-activity calories in the day window

- Decision: Retrieve activities in a single-day window and sum per-activity calorie
  values.
- Rationale: Per-activity calories directly represent activity burn and avoids summary
  aggregation ambiguity.
- Alternatives considered:
  - Use summary endpoint calories: rejected because it may reflect week-level totals.
  - Fetch every activity detail and sum there: rejected as default due to additional
    API cost when list responses already include calories.

## Decision 4: Handle missing per-activity calories as zero contribution

- Decision: Activities with null/missing/invalid calorie values contribute zero, while
  valid activity calories are still summed.
- Rationale: Keeps sensor deterministic and resilient when upstream records are
  incomplete.
- Alternatives considered:
  - Fail refresh when any activity lacks calories: rejected because one bad record
    should not invalidate all metrics.
  - Carry forward previous daily total: rejected due to incorrect freshness semantics.

## Decision 5: Use strict no-rollover behavior for day-level activity calories

- Decision: Recompute day-level total each refresh and never reuse prior-day non-null
  values.
- Rationale: Day-scoped values must reflect the current calculation day only.
- Alternatives considered:
  - Reuse cached value on missing data: rejected because it can show stale totals for
    a different day.

## Decision 6: Isolate day-activity fetch errors from unrelated metrics where possible

- Decision: Treat day-level activity aggregation as an independent payload slice so
  existing summary/wellness metrics can remain available when only this slice fails.
- Rationale: Reduces blast radius and improves user trust in unaffected entities.
- Alternatives considered:
  - Fail whole coordinator update on activity-slice error: rejected as too disruptive.

## Decision 7: Deduplicate by activity identifier before summation

- Decision: Ensure each activity ID is counted once per refresh.
- Rationale: Protects against duplicate records in edge API responses.
- Alternatives considered:
  - Blindly sum returned rows: rejected because duplicate rows would inflate totals.
