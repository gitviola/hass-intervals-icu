# Intervals.icu for Home Assistant

Expose Intervals.icu training and wellness metrics as Home Assistant sensor entities.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![CI](https://github.com/gitviola/hass-intervals-icu/actions/workflows/ci.yml/badge.svg)](https://github.com/gitviola/hass-intervals-icu/actions/workflows/ci.yml)
[![HACS](https://github.com/gitviola/hass-intervals-icu/actions/workflows/hacs.yml/badge.svg)](https://github.com/gitviola/hass-intervals-icu/actions/workflows/hacs.yml)
[![Hassfest](https://github.com/gitviola/hass-intervals-icu/actions/workflows/hassfest.yml/badge.svg)](https://github.com/gitviola/hass-intervals-icu/actions/workflows/hassfest.yml)

## One-click install

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=gitviola&repository=hass-intervals-icu&category=integration)

After install/restart:

[![Open your Home Assistant instance and start setting up Intervals.icu.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=intervals_icu)

## Quick setup

1. In Intervals.icu, open `/settings`.
2. In **Developer Settings**, generate an API key.
3. Add integration **Intervals.icu** in Home Assistant.
4. Enter:
- `API key`
- `Athlete id` (use `0` for current athlete)

Authentication model:
- Basic Auth username: `API_KEY`
- Basic Auth password: your generated API key

## What it exposes

- Summary metrics (fitness, fatigue, form, training load, eFTP, ramp rate, etc.)
- Wellness metrics (including sleep duration, sleep score, sleep quality)
- Garmin-like derived HRV status metrics:
  - `Overnight HRV` (latest overnight value from Intervals wellness)
  - `HRV Status (7-Day Avg)` (numeric rolling status)
  - `HRV Status (Level)` (`Balanced`/`Unbalanced`/`Low`/`Poor`/`No status`)
  - `HRV Baseline Lower`, `HRV Baseline Upper`, `HRV Low Threshold (7-Day Avg)`
- Dynamic sport wellness metrics from `sportInfo` (for example Ride/Run eFTP, W Prime, P Max)
- Fast same-day change detection: the integration probes Intervals.icu every minute
  using lightweight activity/wellness freshness metadata, then performs a full
  refresh only when today's upstream data changes or the configured full refresh
  interval elapses
- Null rollover logic for persistent metrics (for example HRV, VO2max, resting HR, weight)

HRV age-context source:
- Uses athlete profile fields (`sex`, `icu_date_of_birth`) from Intervals API when available.
- Optional integration setting `Birthdate override (YYYY-MM-DD)` is available if profile birthdate is missing and you want `Poor` classification to use age context.

Full metric inventory:
- [API metrics list](docs/API_METRICS.md)

## Action: set wellness

The integration exposes `intervals_icu.set_wellness` for writing wellness
fields back to Intervals.icu.

Rules:
- If `date` is omitted, Home Assistant local `today` is used.
- Only provided fields are sent; omitted fields are not changed.
- At least one writable field is required.

Writable fields include:
- Body metrics: `weight`, `body_fat`, `abdomen`
- Cardiovascular/recovery: `resting_hr`, `hrv`, `hrv_sdnn`, `vo2max`, `sp_o2`
- Sleep: `sleep_secs`, `sleep_score`, `sleep_quality`, `avg_sleeping_hr`
- Wellness scales: `soreness`, `fatigue`, `stress`, `mood`, `motivation`, `injury`, `hydration`
- Nutrition/metabolic: `kcal_consumed`, `carbohydrates`, `protein`, `fat_total`
- Other wellness values: `systolic`, `diastolic`, `respiration`, `steps`,
  `readiness`, `baevsky_si`, `blood_glucose`, `lactate`, `menstrual_phase`,
  `hydration_volume`, `comments`, `temp_weight`, `temp_resting_hr`

Example (today):

```yaml
action: intervals_icu.set_wellness
data:
  weight: 72.4
  protein: 160
  carbohydrates: 240
```

Example with dynamic values (YAML mode in Actions / Developer Tools):

```yaml
action: intervals_icu.set_wellness
data:
  weight: "{{ states('input_number.martin_body_weight') }}"
  body_fat: "{{ states('sensor.martin_body_weight_body_fat') }}"
  resting_hr: "{{ states('sensor.some_resting_hr_sensor') }}"
```

Example (explicit date):

```yaml
action: intervals_icu.set_wellness
data:
  date: "2026-03-24"
  kcal_consumed: 2450
  fat_total: 75
  hydration_volume: 2500
```

## Development

### Local check

```bash
python3 -m compileall custom_components/intervals_icu
```

### Local Home Assistant (Docker dev mode)

Run Home Assistant locally with this integration bind-mounted for fast manual
testing.

1. Create local Home Assistant state dir (fully git-ignored):

```bash
mkdir -p .homeassistant
```

2. Start Home Assistant:

```bash
docker compose up -d homeassistant
```

3. Open http://localhost:8123 and complete onboarding.
4. Add **Intervals.icu** in Home Assistant.

Notes:
- Integration source is mounted directly from `custom_components/intervals_icu`
  to `/config/custom_components/intervals_icu` in the container.
- No copy step is needed for code changes.
- Python bytecode cache is disabled (`PYTHONDONTWRITEBYTECODE=1`) to reduce
  stale cache issues while iterating.
- Most Python/backend changes require a Home Assistant restart:

```bash
docker compose restart homeassistant
```

- Stream logs:

```bash
docker compose logs -f homeassistant
```

- Stop local Home Assistant:

```bash
docker compose down
```

## Publishing checklist

See:
- [Publishing guide](docs/PUBLISHING.md)

## License

MIT. See [LICENSE](LICENSE).

### Trademark Notice

Intervals.icu name and logo are property of Intervals.icu and used here for
identification/compatibility purposes only.

## References

- Intervals.icu API docs: [intervals.icu/api-docs.html](https://intervals.icu/api-docs.html)
- Intervals.icu OpenAPI: [intervals.icu/api/v1/docs](https://intervals.icu/api/v1/docs)
- Intervals.icu API access guide: [forum post](https://forum.intervals.icu/t/api-access-to-intervals-icu/609)
- HACS general publish requirements: [hacs.xyz/docs/publish/start](https://www.hacs.xyz/docs/publish/start/)
- HACS integration requirements: [hacs.xyz/docs/publish/integration](https://www.hacs.xyz/docs/publish/integration/)
- HACS My links: [hacs.xyz/docs/use/my](https://www.hacs.xyz/docs/use/my/)
- HA integration docs (file structure, manifest, config flow):
  - [File structure](https://developers.home-assistant.io/docs/creating_integration_file_structure/)
  - [Manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
  - [Config flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
