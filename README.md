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
- Dynamic sport wellness metrics from `sportInfo` (for example Ride/Run eFTP, W Prime, P Max)
- Null rollover logic for persistent metrics (for example HRV, VO2max, resting HR, weight)

Full metric inventory:
- [API metrics list](docs/API_METRICS.md)

## Development

### Local check

```bash
python3 -m compileall custom_components/intervals_icu
```

### Manual install for local testing

Copy this folder into Home Assistant config:

`<config>/custom_components/intervals_icu`

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
