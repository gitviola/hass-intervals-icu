# Data Model: Daily Activity Calories Sensor

## Entity: DailyActivityWindow

- date: string (`YYYY-MM-DD`, Home Assistant local date)
- oldest: string (ISO-8601 local date-time lower bound for the day)
- newest: string (ISO-8601 local date-time upper bound for the day)

Rules:
- Window MUST represent exactly one local calendar day.
- Window boundaries MUST be recomputed each refresh.

## Entity: ActivityCaloriesInput

- id: string (activity identifier, required)
- start_date_local: string | optional (local start date-time)
- calories: int | optional

Validation and normalization:
- Rows without `id` are ignored.
- `calories` contributes only when numeric and non-negative.
- Duplicate `id` values are deduplicated before aggregation.

## Entity: DailyActivityCaloriesAggregate

- calculation_date: string (`YYYY-MM-DD`)
- total_calories: int (sum of valid activity calories for calculation_date)
- activity_count_total: int (number of unique activities evaluated)
- activity_count_with_calories: int (number of activities contributing calories)
- activity_count_missing_calories: int (unique activities with missing/invalid calories)
- source_status: string (`ok` or `partial` or `error`)
- error: string | optional

State semantics:
- No activities for date -> `total_calories = 0`, status `ok`.
- Missing calories for some activities -> status `partial`, valid values still summed.
- Fetch failure -> status `error`, no stale cross-day carry-forward.

## Entity: CoordinatorDataExtension

- activity_daily: object (new coordinator source for day-level calories data)
  - calories: int | null
  - calculation_date: string | null
  - status: string
  - diagnostics: object (counts/error metadata as needed)

Rules:
- Existing `summary` and `wellness` payloads remain unchanged in meaning.
- `activity_daily` MUST be I/O-free at entity read time (computed during refresh).

## Entity: DailyActivityCaloriesSensor

- key: stable sensor key for new entity
- name: user-facing name indicating day-level activity calories
- native_unit_of_measurement: `kcal`
- value source: `CoordinatorDataExtension.activity_daily.calories`
- attributes: includes `calculation_date` and optional diagnostics

Behavior:
- Value reflects one calculation day only.
- Value does not roll over from prior day totals.
