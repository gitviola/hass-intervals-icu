# Contract: Home Assistant Wellness Write Service

## Service Name

`intervals_icu.set_wellness`

## Request Schema

- `date`: string (optional, ISO-8601 `YYYY-MM-DD`)
- `weight`: number (optional)
- `kcal_consumed`: integer (optional)
- `carbohydrates`: number (optional)
- `protein`: number (optional)
- `fat_total`: number (optional)
- `hydration_volume`: number (optional)

## Request Rules

- At least one writable field is required:
  - `weight`, `kcal_consumed`, `carbohydrates`, `protein`, `fat_total`, `hydration_volume`
- If `date` omitted, use Home Assistant local date.
- Omitted writable fields MUST NOT be sent to Intervals API.

## Mapping to Intervals Wellness API

- `weight` -> `weight`
- `kcal_consumed` -> `kcalConsumed`
- `carbohydrates` -> `carbohydrates`
- `protein` -> `protein`
- `fat_total` -> `fatTotal`
- `hydration_volume` -> `hydrationVolume`

Endpoint:
- `PUT /api/v1/athlete/{id}/wellness/{date}`

## Response/Outcome Contract

On success:
- service call returns successfully
- coordinator refresh is requested

On failure:
- service call fails with actionable error
- no assumption of local state changes
