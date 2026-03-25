# Quickstart: Wellness Data Write Support

## 1) Reload integration code

- Install/reload updated custom component in Home Assistant.
- Restart HA or reload the integration.

## 2) Call service/action without date (defaults to today)

Example data:

```yaml
weight: 72.4
kcal_consumed: 2550
protein: 165
carbohydrates: 290
fat_total: 78
```

Expected:
- Target date resolves to HA local today.
- Only listed fields are updated.

## 3) Call service/action with explicit date

Example data:

```yaml
date: "2026-03-20"
weight: 72.1
```

Expected:
- Only weight for 2026-03-20 is updated.
- Other wellness fields on that date remain unchanged.

## 4) Validate partial update safety

- Confirm a pre-existing field (for example `protein`) remains unchanged when not included.

## 5) Validate error handling

- Send request with no writable fields and verify clear validation failure.
- Send request with invalid date and verify clear validation failure.
