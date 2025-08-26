#!/bin/bash

# Generate sample billing data for any month (current or past)
# This script creates an API token named after the month and generates random RequestLog and RequestImage data

set -e  # Exit on error

echo "=========================================="
echo "Billing Data Generator"
echo "=========================================="
echo ""

# Default values
MONTH=""
YEAR=""
USER_EMAIL="demo@example.com"
MIN_REQUESTS=10
MAX_REQUESTS=30
PAYMENT_STATUS=""

# Function to show help
show_help() {
    echo "Usage: $0 --month MONTH --year YEAR [options]"
    echo ""
    echo "Required Arguments:"
    echo "  --month MONTH    Month number (1-12)"
    echo "  --year YEAR      Year (e.g., 2025)"
    echo ""
    echo "Optional Arguments:"
    echo "  --email EMAIL    User email address (default: demo@example.com)"
    echo "  --min N          Minimum requests per day (default: 10)"
    echo "  --max N          Maximum requests per day (default: 30)"
    echo "  --status STATUS  Payment status: paid, pending, overdue, or waived"
    echo "                   (auto-determined if not specified)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Generate for August 2025 (current month)"
    echo "  $0 --month 8 --year 2025"
    echo ""
    echo "  # Generate for June 2025 with overdue status"
    echo "  $0 --month 6 --year 2025 --status overdue"
    echo ""
    echo "  # Generate for July 2025 with specific user and paid status"
    echo "  $0 --month 7 --year 2025 --email user@example.com --status paid"
    echo ""
    echo "  # Generate with more requests per day"
    echo "  $0 --month 5 --year 2025 --min 50 --max 100"
    echo ""
    echo "Notes:"
    echo "  - Cannot generate data for future months"
    echo "  - Current month is always set to 'pending' status"
    echo "  - Past months default to 'paid' (odd months) or 'overdue' (even months)"
    echo "  - API token name will be the month name in uppercase (e.g., JANUARY, FEBRUARY)"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --month)
            MONTH="$2"
            shift 2
            ;;
        --year)
            YEAR="$2"
            shift 2
            ;;
        --email)
            USER_EMAIL="$2"
            shift 2
            ;;
        --min)
            MIN_REQUESTS="$2"
            shift 2
            ;;
        --max)
            MAX_REQUESTS="$2"
            shift 2
            ;;
        --status)
            PAYMENT_STATUS="$2"
            if [[ "$PAYMENT_STATUS" != "paid" && "$PAYMENT_STATUS" != "pending" && "$PAYMENT_STATUS" != "overdue" && "$PAYMENT_STATUS" != "waived" ]]; then
                echo "Error: Invalid payment status. Must be 'paid', 'pending', 'overdue', or 'waived'"
                exit 1
            fi
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$MONTH" ] || [ -z "$YEAR" ]; then
    echo "Error: --month and --year are required arguments"
    echo ""
    show_help
    exit 1
fi

# Validate month range
if [ "$MONTH" -lt 1 ] || [ "$MONTH" -gt 12 ]; then
    echo "Error: Month must be between 1 and 12"
    exit 1
fi

# Get month name
case $MONTH in
    1) MONTH_NAME="January" ;;
    2) MONTH_NAME="February" ;;
    3) MONTH_NAME="March" ;;
    4) MONTH_NAME="April" ;;
    5) MONTH_NAME="May" ;;
    6) MONTH_NAME="June" ;;
    7) MONTH_NAME="July" ;;
    8) MONTH_NAME="August" ;;
    9) MONTH_NAME="September" ;;
    10) MONTH_NAME="October" ;;
    11) MONTH_NAME="November" ;;
    12) MONTH_NAME="December" ;;
esac

echo "Configuration:"
echo "  Period: $MONTH_NAME $YEAR"
echo "  User Email: $USER_EMAIL"
echo "  Requests per day: $MIN_REQUESTS - $MAX_REQUESTS"
if [ -n "$PAYMENT_STATUS" ]; then
    echo "  Payment Status: $PAYMENT_STATUS"
else
    echo "  Payment Status: (auto-determined)"
fi
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the Django project root."
    exit 1
fi

# Build the Django command
CMD="uv run python manage.py generate_billing_data"
CMD="$CMD --month $MONTH --year $YEAR"
CMD="$CMD --user-email \"$USER_EMAIL\""
CMD="$CMD --min-requests-per-day $MIN_REQUESTS"
CMD="$CMD --max-requests-per-day $MAX_REQUESTS"

if [ -n "$PAYMENT_STATUS" ]; then
    CMD="$CMD --payment-status $PAYMENT_STATUS"
fi

# Run the Django management command
echo "Generating data for $MONTH_NAME $YEAR..."
echo "----------------------------------------"
eval $CMD

echo ""
echo "=========================================="
echo "Data generation complete!"
echo ""
echo "To view the generated data:"
echo "  1. Access Django admin at: http://localhost:8000/admin/"
echo "  2. Or run: uv run python verify_billing_periods.py"
echo ""
echo "To query the data programmatically:"
echo "  from usage.models import RequestLog, RequestImage, BillingPeriod"
echo "  from customers.models import ApiToken"
echo "  "
echo "  # Get the token for $MONTH_NAME"
MONTH_NAME_UPPER=$(echo "$MONTH_NAME" | tr '[:lower:]' '[:upper:]')
echo "  token = ApiToken.objects.get(name='$MONTH_NAME_UPPER')"
echo "  "
echo "  # Get billing period"
echo "  from datetime import date"
echo "  period = BillingPeriod.objects.get("
echo "      period_start=date($YEAR, $MONTH, 1)"
echo "  )"
echo "  print(f'Status: {period.payment_status}')"
echo "  print(f'Total: \${period.total_cost_cents / 100:.2f}')"
echo "=========================================="
