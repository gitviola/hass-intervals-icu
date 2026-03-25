# Data Model: Wellness Data Write Support

## Entity: WellnessWriteRequest

- date: string | optional | ISO-8601 local date (`YYYY-MM-DD`)
- weight: float | optional
- kcal_consumed: int | optional
- carbohydrates: float | optional
- protein: float | optional
- fat_total: float | optional
- hydration_volume: float | optional

Validation:
- At least one writable field MUST be provided (date alone is invalid).
- `date` if provided MUST be valid ISO-8601 day string.
- Numeric fields MUST be finite numbers.

## Entity: IntervalsWellnessPatchPayload

Payload sent to Intervals API (`Wellness` partial):
- id (optional when using date path endpoint)
- weight -> `weight`
- kcal_consumed -> `kcalConsumed`
- carbohydrates -> `carbohydrates`
- protein -> `protein`
- fat_total -> `fatTotal`
- hydration_volume -> `hydrationVolume`

Rule:
- Include only explicitly provided writable keys.

## Entity: WellnessWriteResult

- success: bool
- athlete_id: string
- date: string
- updated_fields: list[string]
- error: string | optional

State transitions:
1. Request validated
2. Payload mapped and sent
3. If API success -> coordinator refresh requested -> success result
4. If API fail -> no local mutation -> error result
