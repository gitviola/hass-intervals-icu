# Contract: Daily Activity Calories Sensor

## Home Assistant Entity Contract

### Existing Entity (unchanged)

- Summary calories entity remains available with existing semantics and source.

### New Entity

- Entity purpose: Day-level calories burned from activities.
- State type: Numeric.
- Unit: `kcal`.
- Expected state class: measurement-style numeric sensor behavior.

## New Entity Output Rules

- State equals sum of valid per-activity calories for one calculation day.
- If no activities exist for the calculation day, state is `0`.
- Activity rows with missing/invalid calories contribute `0` and do not fail the entity.
- Duplicate activity identifiers are counted once.

## New Entity Attributes

- `calculation_date`: local date (`YYYY-MM-DD`) used for the state computation.
- `source_status`: `ok` or `partial` or `error`.
- Optional diagnostics:
  - `activity_count_total`
  - `activity_count_with_calories`
  - `activity_count_missing_calories`

## Upstream Data Contract (Intervals API Read)

- Read day-window activities for the configured athlete.
- Minimum fields required from each activity row:
  - `id`
  - `start_date_local` (optional for diagnostics/filtering)
  - `calories`

Contract expectations:
- Endpoint responses may contain missing calorie values.
- Day-level metric must remain deterministic under partial data.

## Backward Compatibility Contract

- Existing summary calories entity and semantics MUST NOT change.
- Existing entity identifiers MUST remain stable.
- New daily activity calories entity introduces additive behavior only.
