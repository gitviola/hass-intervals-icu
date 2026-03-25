# Quickstart: Garmin-Like HRV Status and Baseline Ranges

## 1) Reload integration code

- Install/reload the updated custom component in Home Assistant.
- Restart Home Assistant or reload the `intervals_icu` config entry.

## 2) Verify new entities are created

Confirm these entities exist:
- `HRV Status` (numeric)
- `HRV Status (Level)` (text)
- `HRV Baseline Lower` (numeric)
- `HRV Baseline Upper` (numeric)
- `HRV Low Threshold` (numeric)

Also confirm existing `wellness_hrv` remains unchanged.

## 3) Validate bootstrap from historical wellness HRV

- Start with no prior derived HRV status cache.
- Ensure Intervals has historical overnight HRV values (ideally >= 21 days).
- Trigger a coordinator refresh.
- Confirm derived HRV status and baseline values appear in one refresh cycle.

## 4) Validate status-level mapping

Using a controlled dataset (or staged wellness edits), verify:
- In-range seven-day status value -> `Balanced`.
- Slightly outside baseline, not below low cutoff -> `Unbalanced`.
- Below low cutoff -> `Low`.
- Persistent below age-norm lower bound -> `Poor`.
- Insufficient recent data -> `No status`.

## 5) Validate cache and incremental recompute behavior

- Trigger two refreshes with unchanged wellness HRV source data.
- Confirm second refresh reuses cached derivation (no full recompute path).
- Add or modify one recent HRV data point and refresh again.
- Confirm recalculation occurs and values update.

## 6) Validate chart readiness in Home Assistant

- Add `HRV Status`, `HRV Baseline Lower`, and `HRV Baseline Upper` to a
  `history-graph` or `statistics-graph` card.
- Confirm trend and boundaries can be plotted together over time.
- Optional: validate range-band rendering with `apexcharts-card`.

## 7) Run minimal static validation

```bash
python3 -m compileall custom_components/intervals_icu
```
