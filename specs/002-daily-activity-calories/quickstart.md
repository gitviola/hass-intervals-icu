# Quickstart: Daily Activity Calories Sensor

## 1) Reload integration code

- Install/reload the updated custom component in Home Assistant.
- Restart Home Assistant or reload the `intervals_icu` config entry.

## 2) Validate day-level calories against known activities

- Pick a local date with known activities and known per-activity calories.
- Compute expected sum manually (example: `420 + 610 = 1030`).
- Confirm the new daily activity calories sensor reports the same value.

## 3) Validate summary calories backward compatibility

- Check existing summary calories sensor before and after update.
- Confirm entity remains present and continues to represent summary semantics.

## 4) Validate no-activity day behavior

- Pick a local day with zero activities.
- Confirm daily activity calories sensor reports `0`.

## 5) Validate partial data behavior

- Use a day where at least one activity has no calorie value.
- Confirm sensor still updates and sums only valid calorie values.

## 6) Validate date clarity

- Confirm the sensor exposes the calculation date attribute.
- Trigger another refresh and verify date/value pair remains consistent for the same day.

## 7) Run minimal static validation

```bash
python3 -m compileall custom_components/intervals_icu
```
