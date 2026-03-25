# Intervals.icu Metrics Exposed

The integration currently exposes the metric fields from these Intervals.icu API responses:

- `GET /api/v1/athlete/{id}/athlete-summary.json` (latest summary row)
- `GET /api/v1/athlete/{id}/activities` (current local-day activity slice for daily calories)
- `GET /api/v1/athlete/{id}/wellness/{date}` (latest wellness record)
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
