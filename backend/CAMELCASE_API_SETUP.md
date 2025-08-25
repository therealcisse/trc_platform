# CamelCase JSON API Configuration

This document explains how the Django REST Framework API has been configured to automatically convert between Python's snake_case naming convention and JavaScript's camelCase convention.

## Overview

The Django models use snake_case field names (e.g., `total_cost_cents`), but the API returns camelCase JSON (e.g., `totalCostCents`) to match JavaScript/TypeScript conventions and the TypeScript models defined in `models.ts`.

## Implementation

### 1. Package Installation

We use the `djangorestframework-camel-case` package:

```bash
uv add djangorestframework-camel-case
```

### 2. Django Settings Configuration

In `config/settings.py`, the REST_FRAMEWORK settings have been updated:

```python
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ],
    # ... other settings
    "JSON_UNDERSCOREIZE": {
        "no_underscore_before_number": True,
    },
}
```

### 3. How It Works

#### Outgoing Responses (Django → Client)
- Django model fields: `total_cost_cents`, `period_start`, `is_current`
- API JSON response: `totalCostCents`, `periodStart`, `isCurrent`

#### Incoming Requests (Client → Django)
- Client sends: `{"newPassword": "secret123", "oldPassword": "old123"}`
- Django receives: `{"new_password": "secret123", "old_password": "old123"}`

### 4. Example Transformation

**Django Model (snake_case):**
```python
class BillingPeriod(models.Model):
    period_start = models.DateField()
    period_end = models.DateField()
    total_requests = models.IntegerField()
    total_cost_cents = models.IntegerField()
    is_current = models.BooleanField()
```

**API Response (camelCase):**
```json
{
  "id": "0050317c-6c54-42b7-b034-5aae852db04e",
  "periodStart": "2025-08-01",
  "periodEnd": "2025-08-31",
  "totalRequests": 0,
  "totalCostCents": 0,
  "isCurrent": true,
  "periodLabel": "August 2025",
  "lastRequestAt": null
}
```

**TypeScript Interface (camelCase):**
```typescript
export interface BillingPeriod {
  id: string;
  periodStart: Date;
  periodEnd: Date;
  totalRequests: number;
  totalCostCents: number;
  isCurrent: boolean;
  periodLabel?: string;
  // ... other fields
}
```

## Benefits

1. **Consistency**: Frontend TypeScript code uses native JavaScript camelCase conventions
2. **No Manual Conversion**: Automatic transformation in both directions
3. **Type Safety**: TypeScript interfaces match API responses exactly
4. **Maintainability**: Django models keep Pythonic snake_case naming
5. **Backwards Compatibility**: Existing Django admin and internal code continues to work

## Testing

Run the test script to verify the conversion:

```bash
uv run python test_camelcase.py
```

## API Endpoints Affected

All REST API endpoints automatically use camelCase, including:

- `/api/customers/current-billing-period/` - Current billing period
- `/api/customers/billing-periods/` - List billing periods
- `/api/customers/usage/requests/` - Usage requests
- `/api/customers/tokens/` - API tokens
- All other REST endpoints

## Considerations

1. **Django Admin**: The Django admin interface continues to use snake_case
2. **Database**: Database column names remain in snake_case
3. **Internal Code**: Python code continues to use snake_case
4. **API Only**: Only the JSON API input/output is affected

## Troubleshooting

If a field is not being converted:

1. Check that the field is included in the serializer's `fields` list
2. Verify the REST_FRAMEWORK settings are properly configured
3. Ensure the view is using Response from rest_framework
4. Check for any manual JSON encoding that bypasses the renderer

## Related Files

- `config/settings.py` - Django REST Framework configuration
- `models.ts` - TypeScript model definitions (camelCase)
- `usage/serializers.py` - Example serializers
- `customers/views.py` - Example views using serializers
- `test_camelcase.py` - Test script for verification
