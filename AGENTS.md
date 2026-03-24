# AGENTS.md

## Purpose
Build and maintain a Home Assistant custom integration (`intervals_icu`) that maps Intervals.icu API data to Home Assistant sensors.

## Guardrails
- Keep changes inside this repository.
- Never commit secrets, API keys, or tokens.
- Preserve Home Assistant integration domain: `intervals_icu`.
- Prefer additive, minimal-risk changes.

## Technical defaults
- Use config entries + config flow for setup.
- Use `DataUpdateCoordinator` for shared polling.
- Use typed, async Python code.
- Keep sensor logic in `sensor.py` and API calls in `api.py`.

## Validation
Before finalizing significant changes:
1. Run `python3 -m compileall custom_components/intervals_icu`.
2. Ensure manifest and translations stay in sync with config/options flow fields.
3. Confirm no credentials appear in tracked files.
