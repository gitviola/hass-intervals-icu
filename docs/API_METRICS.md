# Intervals.icu Metrics Exposed

The integration currently exposes the metric fields from these Intervals.icu API responses:

- `GET /api/v1/athlete/{id}/athlete-summary.json` (latest summary row)
- `GET /api/v1/athlete/{id}/activities` (current local-day activity slice for daily calories)
- `GET /api/v1/athlete/{id}/wellness/{date}` (latest wellness record)
- `GET /api/v1/athlete/{id}/wellness.json` (bounded wellness history for HRV status derivation)
- `GET /api/v1/athlete/{id}` (athlete profile fields used for age-context HRV interpretation)
- `wellness.sportInfo[]` flattened to per-sport sensors (for example ride/run eFTP, W Prime, P Max)

## Summary Metrics

- `fitness`
- `fatigue`
- `form`
- `training_load`
- `rampRate`
- `eftp`
- `eftpPerKg`
- `srpe`
- `count`
- `time`
- `moving_time`
- `elapsed_time`
- `distance`
- `total_elevation_gain`
- `calories`
- `weight`
- `timeInZonesTot`

Notes:
- `summary.calories` follows athlete summary semantics and may represent a period aggregate
  (for example week-level totals), not strictly current-day activity burn.

## Daily Activity Metrics

- `calories` (summed from same-day activities)

Daily activity calories semantics:
- Source of truth is per-activity calories from activity rows for one local calendar day.
- Missing/invalid per-activity calories contribute `0` and do not fail aggregation.
- No activity rows for the day yields `0` calories.
- Metric includes `calculation_date` attribute for date clarity.

## Wellness Metrics

- `ctl`
- `atl`
- `rampRate`
- `ctlLoad`
- `atlLoad`
- `sleepSecs`
- `sleepScore`
- `sleepQuality`
- `avgSleepingHR`
- `restingHR`
- `hrv`
- `hrvSDNN`
- `soreness`
- `fatigue`
- `stress`
- `mood`
- `motivation`
- `injury`
- `spO2`
- `systolic`
- `diastolic`
- `hydration`
- `hydrationVolume`
- `readiness`
- `baevskySI`
- `bloodGlucose`
- `lactate`
- `bodyFat`
- `abdomen`
- `vo2max`
- `steps`
- `respiration`
- `kcalConsumed`
- `carbohydrates`
- `protein`
- `fatTotal`
- `weight`
- `menstrualPhase`
- `menstrualPhasePredicted`
- `tempWeight`
- `tempRestingHR`
- `locked`
- `comments`
- `id`
- `updated`

## Null/Rollover Behavior

When a new day includes `null` values:

- Last non-null value is kept for persistent metrics (for example `hrv`, `vo2max`, `restingHR`, `weight`).
- These metrics intentionally **do not** roll over and become unavailable if null:
  - sleep fields (`sleepSecs`, `sleepScore`, `sleepQuality`, `avgSleepingHR`)
  - `steps`
  - nutrition/food fields (`kcalConsumed`, `carbohydrates`, `protein`, `fatTotal`)
  - `hydrationVolume`

## Humanized Scale Sensors

The integration also exposes additional text sensors for key wellness scales:

- `Sleep Quality (Level)`
- `Soreness (Level)`
- `Wellness Fatigue (Level)`
- `Stress (Level)`
- `Mood (Level)`
- `Motivation (Level)`
- `Injury (Level)`
- `Hydration (Level)`

These are derived from the numeric wellness fields using Intervals.icu UI-style labels.

## Derived HRV Status Metrics

The integration also derives Garmin-like HRV status outputs from overnight wellness HRV:

- `Overnight HRV` (latest overnight HRV value from Intervals wellness `hrv`)
- `HRV Status (7-Day Avg)` (rolling 7-day mean of overnight HRV, min 6 samples)
- `HRV Status (Level)` (`Balanced`, `Unbalanced`, `Low`, `Poor`, `No status`)
- `HRV Baseline Lower` (personal baseline low bound from lagged long-window overnight HRV percentiles)
- `HRV Baseline Upper` (personal baseline high bound from lagged long-window overnight HRV percentiles)
- `HRV Low Threshold (7-Day Avg)` (well-below-baseline cutoff below lower baseline bound)

Status semantics:
- `Balanced`: status value is inside baseline range.
- `Unbalanced`: status value is outside baseline range but not low/poor.
- `Low`: status value is below low threshold.
- `Poor`: persistent low-vs-age context condition (with age from athlete profile birthdate/sex, or optional birthdate override setting).
- `No status`: insufficient recent data for a reliable 7-day status value. Baseline
  bounds may still be available during gap recovery if enough older overnight HRV
  history exists.

Efficiency semantics:
- Uses coordinator-side source fingerprinting and cache reuse when wellness HRV inputs are unchanged.
- Recomputes derivation when new or corrected wellness HRV values are detected.
- `HRV Status (7-Day Avg)` exposes a compact `history_28d` attribute for charting bootstrap:
  - `v`: schema version
  - `d`: ISO dates (max 28)
  - `o`: overnight HRV values
  - `s`: 7-day status values
  - `bl`: baseline lower values
  - `bh`: baseline upper values
  - `lv`: compact status codes (`b`, `u`, `l`, `p`, `n`)

Current baseline derivation shape:
- Baseline window: 28 days of lagged overnight HRV history during normal operation.
- Seasoned-history mode: once enough lagged history exists, baseline shifts to a
  56-day lagged lookback to better match Garmin's slower-moving mature baseline.
- Gap recovery: if the lagged 28-day slice is too sparse, baseline recovery expands
  the lagged lookback up to 66 days to preserve Garmin-like continuity across watch/data gaps.
- Early bootstrap: if lagged history is still too short on a new account, baseline
  falls back to the recent unlagged 28-day slice once at least 12 overnight samples exist.
- Baseline lag: 6 days (reduces immediate pull from very recent overnight dips/spikes).
- Baseline bounds:
  - Normal dense-history mode: 32nd and 97th percentiles.
  - Seasoned-history mode: 32nd and 95th percentiles.
  - Gap-recovery mode: 33rd and 95th percentiles.
- Low threshold: below baseline lower bound by at least 2 ms (or 25% of baseline width, whichever is larger).
