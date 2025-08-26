# Billing Period Data Generation Suite

This directory contains a unified billing data generator for creating sample billing period data to demonstrate various billing scenarios in the application.

## Overview

The unified generator can create billing data for any month (current or past) with appropriate payment statuses and API tokens.

## Unified Billing Data Generator

```bash
./generate_billing_data.sh --month MONTH --year YEAR [options]

Required Arguments:
  --month MONTH    Month number (1-12)
  --year YEAR      Year (e.g., 2025)

Optional Arguments:
  --email EMAIL    User email address (default: demo@example.com)
  --min N          Minimum requests per day (default: 10)
  --max N          Maximum requests per day (default: 30)
  --status STATUS  Payment status: paid, pending, overdue, or waived
                   (auto-determined if not specified)
```

### Key Features:
- **No Future Data**: Cannot generate data for future months
- **Current Month**: Always set to 'pending' status
- **Past Months**: Default to 'paid' (odd months) or 'overdue' (even months) if status not specified
- **API Tokens**: Named after the month in uppercase (e.g., JANUARY, FEBRUARY, MARCH)

## Verification Tools

### Comprehensive Billing Period Verification
```bash
uv run python verify_billing_periods.py
```

Shows detailed information for all billing periods including:
- Payment status with color coding
- Request statistics and performance metrics
- Daily request distribution
- Error breakdowns
- API token information


## Usage Scenarios

### Scenario 1: User with Multiple Overdue Periods
```bash
# Create June as overdue
./generate_billing_data.sh --month 6 --year 2025 --email user@example.com --status overdue

# Create July as overdue
./generate_billing_data.sh --month 7 --year 2025 --email user@example.com --status overdue

# Create August as current (pending)
./generate_billing_data.sh --month 8 --year 2025 --email user@example.com

# Verify
uv run python verify_billing_periods.py
```

### Scenario 2: User with Mixed Payment History
```bash
# June was waived (beta testing)
./generate_billing_data.sh --month 6 --year 2025 --email beta@example.com --status waived

# July was paid on time
./generate_billing_data.sh --month 7 --year 2025 --email beta@example.com --status paid

# August is current (pending)
./generate_billing_data.sh --month 8 --year 2025 --email beta@example.com
```

### Scenario 3: High-Volume User
```bash
# Generate more requests per day for multiple months
./generate_billing_data.sh --month 6 --year 2025 --email enterprise@example.com --min 50 --max 100
./generate_billing_data.sh --month 7 --year 2025 --email enterprise@example.com --min 50 --max 100
./generate_billing_data.sh --month 8 --year 2025 --email enterprise@example.com --min 50 --max 100
```

### Scenario 4: Generate Historical Data
```bash
# Generate 6 months of historical data
for month in 3 4 5 6 7 8; do
    ./generate_billing_data.sh --month $month --year 2025 --email historical@example.com
done
```

## Generated Data Details

### API Tokens
Each month creates its own API token named after the month:
- **JANUARY**, **FEBRUARY**, **MARCH**, etc.
- Token names are always uppercase
- Tokens are reused if they already exist for the user

### Request Logs
- Success rate varies by age (85-90% success)
- Random error codes for failed requests
- Various result types (math, captcha, OCR, patterns)
- Proper timestamp distribution throughout each day

### Request Images
- Generated for 70-80% of successful requests
- Random dimensions and content
- Includes shapes, text, and visual elements
- JPEG format with varying quality

### Billing Periods
- Automatic cost calculation ($0.01 per request)
- Proper status flags (is_current, payment_status)
- Payment metadata for paid periods
- Overdue tracking with days calculation

## Payment Status Meanings

- **PENDING**: Current billing period, not yet due
- **PAID**: Payment received and processed
- **OVERDUE**: Payment is past due and requires immediate attention
- **WAIVED**: Charges have been forgiven (promotional, beta testing, etc.)

## Database Cleanup

To remove all generated test data:

```python
# Django shell
from usage.models import RequestLog, RequestImage, BillingPeriod
from customers.models import User, ApiToken

# Remove for specific user
user = User.objects.get(email='demo@example.com')
RequestImage.objects.filter(request_log__user=user).delete()
RequestLog.objects.filter(user=user).delete()
BillingPeriod.objects.filter(user=user).delete()
ApiToken.objects.filter(user=user, name__in=['JUNE', 'JULY', 'AUGUST']).delete()

# Or remove all test billing periods
BillingPeriod.objects.filter(
    period_start__year=2025,
    period_start__month__in=[6, 7, 8]
).delete()
```

## Quick Test Suite

Run the generator for multiple months:
```bash
# Generate complete billing history for demo user
./generate_billing_data.sh --month 6 --year 2025 --status overdue
./generate_billing_data.sh --month 7 --year 2025 --status paid  
./generate_billing_data.sh --month 8 --year 2025  # Current month, auto-pending

# Verify all periods
uv run python verify_billing_periods.py
```

## Example Commands

```bash
# Generate for May 2025 with default settings
./generate_billing_data.sh --month 5 --year 2025

# Generate for January 2025 as paid
./generate_billing_data.sh --month 1 --year 2025 --status paid

# Generate for December 2024 with custom user
./generate_billing_data.sh --month 12 --year 2024 --email olduser@example.com --status overdue

# Generate high-volume February 2025 data
./generate_billing_data.sh --month 2 --year 2025 --min 100 --max 200
```

## Notes

- All scripts use Django transactions for data consistency
- Timestamps are properly distributed across each day
- The scripts respect Django timezone settings
- API tokens are reused if they already exist
- Full tokens are displayed only once during creation
- No secrets are exposed in the output logs

## Troubleshooting

If you encounter issues:
1. Ensure you're in the Django project root directory
2. Check that Django settings are properly configured
3. Verify that the database is accessible
4. Make sure `uv` is installed and configured (per user rules)

For debugging, you can access the Django admin at `http://localhost:8000/admin/` to view and manage the generated data directly.
