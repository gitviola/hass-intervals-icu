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

## Releases
When creating a new release:
1. Decide next semantic version (`MAJOR.MINOR.PATCH`).
2. Update `custom_components/intervals_icu/manifest.json` `version` to match (without `v` prefix).
3. Run validation checks (`python3 -m compileall custom_components/intervals_icu` and CI workflows if available).
4. Commit release changes to `main`.
5. Create an annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
6. Push branch and tag: `git push origin main && git push origin vX.Y.Z`.
7. Publish a GitHub Release for the tag with user-facing notes.

Rules:
- Never retag an existing version.
- Tag format must be `vX.Y.Z`.
