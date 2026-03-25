# Contract: HRV Status and Baseline Sensors

## Home Assistant Entity Contract

### Existing Entity (unchanged)

- `wellness_hrv` remains the latest overnight HRV measurement from wellness
  source data.
- Existing entity identifiers and semantics MUST remain stable.

### New Entities

- `wellness_hrv_status`
  - Purpose: Garmin-like seven-day HRV status numeric value.
  - State type: numeric.
  - Unit: `ms`.
- `wellness_hrv_status_level`
  - Purpose: Humanized Garmin-style status level.
  - State type: text enum.
  - Allowed values: `Balanced`, `Unbalanced`, `Low`, `Poor`, `No status`.
- `wellness_hrv_baseline_lower`
  - Purpose: Personalized lower baseline boundary for current day.
  - State type: numeric.
  - Unit: `ms`.
- `wellness_hrv_baseline_upper`
  - Purpose: Personalized upper baseline boundary for current day.
  - State type: numeric.
  - Unit: `ms`.
- `wellness_hrv_low_threshold`
  - Purpose: Cutoff used to classify `Low`.
  - State type: numeric.
  - Unit: `ms`.

## Status Computation Contract

- Input source: overnight wellness HRV values.
- Status value formula: rolling mean over trailing 7-day window
  (`min_samples_7d = 6`).
- Baseline formula: trailing 21-day personal window (`min_samples_21d = 18`):
  - `baseline_low = mean_21d - 0.5 * sd_21d`
  - `baseline_high = mean_21d + 0.5 * sd_21d`
- Low cutoff formula:
  - `low_cutoff = mean_21d - 1.0 * sd_21d`

Classification precedence:
1. `No status` if data sufficiency is not met.
2. `Poor` if age-norm low condition persists for configured period.
3. `Low` if status value is below low cutoff.
4. `Balanced` if status value is inside baseline range.
5. `Unbalanced` otherwise.

## Entity Attribute Contract

Required attributes on all new entities:
- `calculation_date`: local date used for current computation.
- `source_status`: `ok` or `insufficient_data` or `error`.
- `sample_count_7d`: count of valid HRV samples in status window.
- `sample_count_21d`: count of valid HRV samples in baseline window.

Additional attributes where applicable:
- `age_norm_lower_bound`
- `cache_hit`
- `status_window_days` (constant `7`)
- `baseline_window_days` (constant `21`)

## Upstream Data Contract (Intervals API Read)

- Primary endpoint: `GET /api/v1/athlete/{id}/wellness.json` with bounded
  `oldest/newest` range.
- Optional endpoint: `GET /api/v1/athlete/{id}` for age/sex fields used in
  age-norm assessment.
- `{id}` MUST be the `athlete_id` configured in this integration config entry
  (for example `0` for the authenticated user), not a multi-athlete aggregate.

Minimum wellness fields needed per row:
- `id` (date identifier)
- `hrv`
- `updated` (for dedupe/fingerprint)

Contract expectations:
- Missing/null HRV rows may occur and must be filtered out.
- Historical rows may be corrected upstream and must invalidate cache when
  changed.

## Recalculation and Cache Contract

- Derivation runs in coordinator update path only.
- A normalized fingerprint of input HRV rows determines reuse:
  - Unchanged fingerprint -> do not recompute.
  - Changed fingerprint -> recompute affected trailing window only.
- Bootstrap mode MUST derive from historical data when cache is absent so
  current-day outputs are available within first refresh cycle when possible.

## Backward Compatibility Contract

- Existing entities and service behavior MUST NOT change.
- New HRV status/baseline entities are additive only.
- Humanized text sensor MUST follow project naming convention `(Level)`.
