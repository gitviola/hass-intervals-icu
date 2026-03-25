# Data Model: Garmin-Like HRV Status and Baseline Ranges

## Entity: OvernightHrvSample

- date: string (`YYYY-MM-DD`, Home Assistant local date)
- hrv_ms: float (overnight HRV in milliseconds)
- updated_at: string | optional (upstream last-updated timestamp)
- source_id: string (wellness record id)

Validation and normalization:
- `date` MUST parse as ISO local date.
- `hrv_ms` MUST be numeric and `> 0`.
- Duplicate dates are deduplicated by latest `updated_at`; if timestamps are
  unavailable, last seen record wins.

## Entity: HrvRollingWindows

Per calculation day (`D`):

- samples_7d: list[float] (overnight HRV values in trailing 7-day window)
- samples_21d: list[float] (overnight HRV values in trailing 21-day window)
- sample_count_7d: int
- sample_count_21d: int

Rules:
- `samples_7d` requires minimum 6 valid values.
- `samples_21d` requires minimum 18 valid values.
- If either minimum is unmet, day status resolves to `No status`.

## Entity: DailyHrvDerivedPoint

- date: string (`YYYY-MM-DD`)
- hrv_status_value: float | null
- baseline_mean: float | null
- baseline_sd: float | null
- baseline_low: float | null
- baseline_high: float | null
- low_cutoff: float | null
- age_norm_lower_bound: float | null
- status_level: string (`balanced` | `unbalanced` | `low` | `poor` | `no_status`)
- source_status: string (`ok` | `insufficient_data` | `error`)
- sample_count_7d: int
- sample_count_21d: int

Formula rules when sufficient data exists:
- `hrv_status_value = mean(samples_7d)`
- `baseline_mean = mean(samples_21d)`
- `baseline_sd = stdev(samples_21d)`
- `baseline_low = baseline_mean - 0.5 * baseline_sd`
- `baseline_high = baseline_mean + 0.5 * baseline_sd`
- `low_cutoff = baseline_mean - 1.0 * baseline_sd`

Classification precedence:
1. `no_status` when insufficient samples.
2. `poor` when age-norm breach persistence is active.
3. `low` when `hrv_status_value < low_cutoff`.
4. `balanced` when `baseline_low <= hrv_status_value <= baseline_high`.
5. `unbalanced` otherwise.

## Entity: AgeNormReferenceBand

- sex: string (`female` | `male` | `unknown`)
- age_years: int
- lower_bound_rmssd_ms: float
- source: string (reference dataset/version)

Rules:
- If sex/age unavailable, age-norm evaluation is skipped (`age_norm_lower_bound`
  remains null).
- Reference table MUST be versioned and replaceable without changing sensor IDs.

## Entity: HrvDerivationCache

- source_fingerprint: string (hash of normalized input tuples)
- history_start_date: string
- history_end_date: string
- derived_points_by_date: dict[string, DailyHrvDerivedPoint]
- latest_date: string | null
- latest_point: DailyHrvDerivedPoint | null

Cache behavior:
- Fingerprint unchanged -> reuse `latest_point` and previously derived payload.
- Fingerprint changed -> recompute only affected trailing range required for
  correct current-day outputs.
- Missing cache -> bootstrap by deriving from bounded historical data.

## Entity: CoordinatorDataExtension

New coordinator payload slice: `wellness_hrv_status`

- value: float | null
- level: string (`balanced` | `unbalanced` | `low` | `poor` | `no_status`)
- baseline_low: float | null
- baseline_high: float | null
- low_cutoff: float | null
- calculation_date: string | null
- source_status: string
- sample_count_7d: int
- sample_count_21d: int
- age_norm_lower_bound: float | null
- cache_hit: bool

Rules:
- Existing `wellness.hrv` (latest overnight HRV) remains unchanged.
- `wellness_hrv_status` is computed during coordinator refresh only.
- Entity reads MUST remain I/O-free.

## Entity: HrvStatusSensorSet

- Numeric sensor: `HRV Status`
- Text sensor: `HRV Status (Level)`
- Numeric sensor: `HRV Baseline Lower`
- Numeric sensor: `HRV Baseline Upper`
- Numeric sensor: `HRV Low Threshold`

Behavior:
- Numeric sensors use `ms` and measurement-style semantics.
- Level sensor uses project `(Level)` naming convention.
- All entities remain additive and do not alter existing sensor meaning.
