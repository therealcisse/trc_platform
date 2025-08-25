# Billing System Implementation Guide

## Overview
A simple billing solution that tracks usage by monthly billing periods, allowing external invoice generation based on usage data.

## Core Components

### 1. Enhanced BillingPeriod Model

Add to `usage/models.py`:

```python
class BillingPeriod(models.Model):
    """Represents a monthly billing period."""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),  # For free credits or special cases
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='billing_periods')
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    total_requests = models.IntegerField(default=0)
    total_cost_cents = models.IntegerField(default=0)
    is_current = models.BooleanField(default=False)
    
    # Payment tracking fields
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending',
        db_index=True
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_amount_cents = models.IntegerField(null=True, blank=True)
    payment_reference = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="External invoice or payment reference number"
    )
    payment_notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'billing_periods'
        unique_together = ['user', 'period_start']
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['user', 'is_current']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['user', 'payment_status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.period_start.strftime('%Y-%m')} - {self.payment_status}"
    
    @property
    def period_label(self):
        """Returns a human-readable period label like 'January 2025'"""
        return self.period_start.strftime('%B %Y')
    
    @property
    def can_be_marked_paid(self):
        """Check if this period can be marked as paid."""
        return not self.is_current and self.payment_status in ['pending', 'overdue']
    
    def mark_as_paid(self, amount_cents=None, reference=None, notes=None):
        """Mark billing period as paid."""
        if self.is_current:
            raise ValueError("Cannot mark current billing period as paid")
        
        if self.payment_status == 'paid':
            raise ValueError("Billing period is already marked as paid")
        
        self.payment_status = 'paid'
        self.paid_at = timezone.now()
        self.paid_amount_cents = amount_cents or self.total_cost_cents
        self.payment_reference = reference
        self.payment_notes = notes
        self.save(update_fields=[
            'payment_status', 
            'paid_at', 
            'paid_amount_cents', 
            'payment_reference',
            'payment_notes',
            'updated_at'
        ])
    
    def mark_as_overdue(self):
        """Mark billing period as overdue."""
        if self.is_current:
            raise ValueError("Cannot mark current billing period as overdue")
        
        if self.payment_status == 'paid':
            raise ValueError("Cannot mark paid billing period as overdue")
        
        self.payment_status = 'overdue'
        self.save(update_fields=['payment_status', 'updated_at'])
    
    def mark_as_waived(self, notes=None):
        """Mark billing period as waived (no payment required)."""
        if self.is_current:
            raise ValueError("Cannot waive current billing period")
        
        self.payment_status = 'waived'
        self.payment_notes = notes
        self.save(update_fields=['payment_status', 'payment_notes', 'updated_at'])
```

### 2. Update RequestLog Model

Add to `usage/models.py`:

```python
# Add this field to RequestLog model
billing_period = models.ForeignKey(
    'BillingPeriod',
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='requests'
)
```

### 3. Helper Functions

Add to `usage/utils.py` or `usage/models.py`:

```python
from django.utils import timezone
from datetime import timedelta

def get_or_create_current_billing_period(user):
    """Get or create billing period for current month."""
    today = timezone.now().date()
    period_start = today.replace(day=1)
    
    # Calculate period end (last day of month)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)
    
    # Mark any previous periods as not current
    BillingPeriod.objects.filter(user=user, is_current=True).update(is_current=False)
    
    # Get or create current period
    billing_period, created = BillingPeriod.objects.get_or_create(
        user=user,
        period_start=period_start,
        defaults={
            'period_end': period_end,
            'is_current': True
        }
    )
    
    if not created and not billing_period.is_current:
        billing_period.is_current = True
        billing_period.save(update_fields=['is_current'])
    
    return billing_period
```

### 4. Update SolveView

Modify `core/views.py` in the `SolveView.post()` method:

```python
# After successful request processing:

# Get current billing period
from usage.utils import get_or_create_current_billing_period
billing_period = get_or_create_current_billing_period(request.user)

# Log request with billing period
request_log = RequestLog.objects.create(
    user=request.user,
    token=getattr(request, 'token', None),
    billing_period=billing_period,  # Add this
    service='core.image_solve',
    duration_ms=duration_ms,
    request_bytes=len(image_bytes),
    response_bytes=len(result['result']),
    status='success',
    request_id=request.request_id,
)

# Update billing period totals
billing_period.total_requests += 1
billing_period.total_cost_cents += settings.cost_per_request_cents
billing_period.save(update_fields=['total_requests', 'total_cost_cents', 'updated_at'])
```

### 5. API Endpoints

Add to `customers/views.py`:

```python
from usage.models import BillingPeriod
from usage.utils import get_or_create_current_billing_period

class BillingPeriodsListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    
    def get(self, request):
        """List all billing periods for the user."""
        periods = BillingPeriod.objects.filter(user=request.user)
        
        # Optional filters
        status = request.query_params.get('status')
        if status:
            periods = periods.filter(payment_status=status)
        
        data = []
        for period in periods:
            data.append({
                'id': str(period.id),
                'period_label': period.period_label,
                'period_start': period.period_start.isoformat(),
                'period_end': period.period_end.isoformat(),
                'total_requests': period.total_requests,
                'total_cost_cents': period.total_cost_cents,
                'is_current': period.is_current,
                'payment_status': period.payment_status,
                'paid_at': period.paid_at.isoformat() if period.paid_at else None,
                'paid_amount_cents': period.paid_amount_cents,
                'payment_reference': period.payment_reference,
            })
        
        return Response({'results': data})


class CurrentBillingPeriodView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    
    def get(self, request):
        """Get current billing period summary."""
        period = get_or_create_current_billing_period(request.user)
        
        # Get last request timestamp
        last_request = RequestLog.objects.filter(
            billing_period=period
        ).order_by('-request_ts').first()
        
        return Response({
            'id': str(period.id),
            'period_label': period.period_label,
            'period_start': period.period_start.isoformat(),
            'period_end': period.period_end.isoformat(),
            'total_requests': period.total_requests,
            'total_cost_cents': period.total_cost_cents,
            'is_current': period.is_current,
            'last_request_at': last_request.request_ts.isoformat() if last_request else None,
        })


class BillingPeriodDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    
    def get(self, request, period_id):
        """Get detailed requests for a billing period."""
        try:
            period = BillingPeriod.objects.get(id=period_id, user=request.user)
        except BillingPeriod.DoesNotExist:
            return Response(
                {'detail': 'Billing period not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get paginated requests
        page = int(request.query_params.get('page', 1))
        page_size = 25
        
        requests_qs = RequestLog.objects.filter(billing_period=period)
        total = requests_qs.count()
        offset = (page - 1) * page_size
        requests = requests_qs[offset:offset + page_size]
        
        request_data = []
        for log in requests:
            request_data.append({
                'id': str(log.id),
                'request_ts': log.request_ts.isoformat(),
                'service': log.service,
                'status': log.status,
                'duration_ms': log.duration_ms,
                'request_bytes': log.request_bytes,
                'response_bytes': log.response_bytes,
                'request_id': str(log.request_id),
            })
        
        return Response({
            'period': {
                'id': str(period.id),
                'period_label': period.period_label,
                'period_start': period.period_start.isoformat(),
                'period_end': period.period_end.isoformat(),
                'total_requests': period.total_requests,
                'total_cost_cents': period.total_cost_cents,
                'payment_status': period.payment_status,
                'paid_at': period.paid_at.isoformat() if period.paid_at else None,
                'payment_reference': period.payment_reference,
            },
            'requests': {
                'results': request_data,
                'count': total,
                'next': page + 1 if offset + page_size < total else None,
                'previous': page - 1 if page > 1 else None,
            }
        })


class MarkBillingPeriodPaidView(APIView):
    """Admin endpoint to mark a billing period as paid."""
    permission_classes = [IsAuthenticated, IsAdminUser]  # Admin only
    
    def post(self, request, period_id):
        """Mark a billing period as paid."""
        try:
            period = BillingPeriod.objects.get(id=period_id)
        except BillingPeriod.DoesNotExist:
            return Response(
                {'detail': 'Billing period not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if period.is_current:
            return Response(
                {'detail': 'Cannot mark current billing period as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if period.payment_status == 'paid':
            return Response(
                {'detail': 'Billing period is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get payment details from request
        amount_cents = request.data.get('amount_cents')
        reference = request.data.get('payment_reference')
        notes = request.data.get('notes')
        
        # Mark as paid
        period.mark_as_paid(
            amount_cents=amount_cents,
            reference=reference,
            notes=notes
        )
        
        return Response({
            'id': str(period.id),
            'payment_status': period.payment_status,
            'paid_at': period.paid_at.isoformat(),
            'paid_amount_cents': period.paid_amount_cents,
            'payment_reference': period.payment_reference,
        })
```

### 6. URL Configuration

Add to `customers/urls.py`:

```python
urlpatterns += [
    # Billing endpoints
    path('billing/current', CurrentBillingPeriodView.as_view(), name='billing-current'),
    path('billing/periods', BillingPeriodsListView.as_view(), name='billing-periods'),
    path('billing/periods/<uuid:period_id>', BillingPeriodDetailView.as_view(), name='billing-period-detail'),
]

# Admin endpoint (could be in a separate admin API or admin urls)
# path('admin/billing/periods/<uuid:period_id>/mark-paid', MarkBillingPeriodPaidView.as_view(), name='admin-mark-paid'),
```

### 7. Django Admin Configuration

Add to `usage/admin.py`:

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import BillingPeriod, RequestLog

@admin.register(BillingPeriod)
class BillingPeriodAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'period_label', 
        'total_requests', 
        'total_cost_cents_display',
        'payment_status_badge',
        'paid_at',
        'payment_reference',
        'is_current'
    ]
    list_filter = ['payment_status', 'is_current', 'period_start']
    search_fields = ['user__email', 'payment_reference']
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['mark_as_paid', 'mark_as_overdue', 'mark_as_waived']
    
    def total_cost_cents_display(self, obj):
        return f"${obj.total_cost_cents / 100:.2f}"
    total_cost_cents_display.short_description = "Total Cost"
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'paid': 'green',
            'overdue': 'red',
            'waived': 'gray',
        }
        color = colors.get(obj.payment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = "Payment Status"
    
    def mark_as_paid(self, request, queryset):
        count = 0
        for period in queryset:
            if period.can_be_marked_paid:
                period.mark_as_paid()
                count += 1
        self.message_user(request, f"{count} billing periods marked as paid.")
    mark_as_paid.short_description = "Mark selected periods as paid"
    
    def mark_as_overdue(self, request, queryset):
        count = 0
        for period in queryset:
            if not period.is_current and period.payment_status != 'paid':
                period.mark_as_overdue()
                count += 1
        self.message_user(request, f"{count} billing periods marked as overdue.")
    mark_as_overdue.short_description = "Mark selected periods as overdue"
    
    def mark_as_waived(self, request, queryset):
        count = 0
        for period in queryset:
            if not period.is_current and period.payment_status not in ['paid', 'waived']:
                period.mark_as_waived()
                count += 1
        self.message_user(request, f"{count} billing periods marked as waived.")
    mark_as_waived.short_description = "Mark selected periods as waived"
```

### 8. Management Commands

Create `usage/management/commands/mark_overdue_periods.py`:

```python
"""
Run monthly to mark unpaid periods as overdue.
Example cron: 0 0 5 * * python manage.py mark_overdue_periods
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from usage.models import BillingPeriod

class Command(BaseCommand):
    help = 'Mark unpaid billing periods as overdue'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days after period end to mark as overdue'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        
        # Mark periods as overdue if they ended > X days ago and are still pending
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        overdue_periods = BillingPeriod.objects.filter(
            period_end__lt=cutoff_date,
            payment_status='pending',
            is_current=False
        )
        
        count = 0
        for period in overdue_periods:
            period.mark_as_overdue()
            count += 1
            self.stdout.write(f'Marked {period} as overdue')
        
        self.stdout.write(
            self.style.SUCCESS(f'Marked {count} billing periods as overdue')
        )
```

Create `usage/management/commands/create_billing_periods.py`:

```python
"""
Create billing periods for existing users.
Run once after implementing the billing system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from usage.utils import get_or_create_current_billing_period

User = get_user_model()

class Command(BaseCommand):
    help = 'Create current billing periods for all active users'
    
    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True)
        count = 0
        
        for user in users:
            period = get_or_create_current_billing_period(user)
            count += 1
            self.stdout.write(f'Created/updated billing period for {user.email}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Processed {count} users')
        )
```

## API Response Schemas

### Current Billing Period Response
```json
{
  "id": "uuid",
  "period_label": "January 2025",
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "total_requests": 42,
  "total_cost_cents": 4200,
  "is_current": true,
  "last_request_at": "2025-01-13T10:30:00Z"
}
```

### Billing Periods List Response
```json
{
  "results": [
    {
      "id": "uuid",
      "period_label": "January 2025",
      "period_start": "2025-01-01",
      "period_end": "2025-01-31",
      "total_requests": 42,
      "total_cost_cents": 4200,
      "is_current": true,
      "payment_status": "pending",
      "paid_at": null,
      "paid_amount_cents": null,
      "payment_reference": null
    },
    {
      "id": "uuid",
      "period_label": "December 2024",
      "period_start": "2024-12-01",
      "period_end": "2024-12-31",
      "total_requests": 128,
      "total_cost_cents": 12800,
      "is_current": false,
      "payment_status": "paid",
      "paid_at": "2025-01-05T14:22:00Z",
      "paid_amount_cents": 12800,
      "payment_reference": "INV-2024-12-001"
    }
  ]
}
```

### Billing Period Detail Response
```json
{
  "period": {
    "id": "uuid",
    "period_label": "December 2024",
    "period_start": "2024-12-01",
    "period_end": "2024-12-31",
    "total_requests": 128,
    "total_cost_cents": 12800,
    "payment_status": "paid",
    "paid_at": "2025-01-05T14:22:00Z",
    "payment_reference": "INV-2024-12-001"
  },
  "requests": {
    "results": [
      {
        "id": "uuid",
        "request_ts": "2024-12-15T10:30:00Z",
        "service": "core.image_solve",
        "status": "success",
        "duration_ms": 412,
        "request_bytes": 58213,
        "response_bytes": 987,
        "request_id": "uuid"
      }
    ],
    "count": 128,
    "next": 2,
    "previous": null
  }
}
```

## Migration Steps

1. **Create and run migrations**:
   ```bash
   python manage.py makemigrations usage
   python manage.py migrate
   ```

2. **Create billing periods for existing users**:
   ```bash
   python manage.py create_billing_periods
   ```

3. **Migrate historical RequestLogs** (create a data migration):
   ```python
   # In a data migration file
   from django.db import migrations
   
   def assign_billing_periods(apps, schema_editor):
       RequestLog = apps.get_model('usage', 'RequestLog')
       BillingPeriod = apps.get_model('usage', 'BillingPeriod')
       
       for log in RequestLog.objects.filter(billing_period__isnull=True):
           # Determine the billing period based on request_ts
           period_start = log.request_ts.date().replace(day=1)
           
           # Get or create the billing period
           period, created = BillingPeriod.objects.get_or_create(
               user=log.user,
               period_start=period_start,
               defaults={
                   'period_end': # calculate last day of month,
                   'is_current': False
               }
           )
           
           # Assign the billing period
           log.billing_period = period
           log.save(update_fields=['billing_period'])
           
           # Update period totals
           period.total_requests += 1
           period.total_cost_cents += 100  # or get from settings
           period.save()
   ```

4. **Set up cron job for overdue marking**:
   ```bash
   # Add to crontab
   0 0 5 * * cd /path/to/project && python manage.py mark_overdue_periods
   ```

## External Invoice Workflow

1. **Monthly process**:
   - Query billing periods with `payment_status='pending'`
   - Generate invoices in external system
   - Use billing period ID as reference

2. **Payment recording**:
   - Mark periods as paid via Django admin
   - Or use the admin API endpoint
   - Include invoice reference number

3. **Customer communication**:
   - Send invoice emails with period details
   - Include link to usage details page
   - Show payment status in customer portal

## Benefits

- **Simple**: Just tracks usage by month
- **No payment complexity**: External invoice handling
- **Clear boundaries**: Monthly billing periods
- **Payment tracking**: Know what's paid/unpaid
- **Audit trail**: Complete payment history
- **Admin-friendly**: Easy bulk operations
- **Flexible statuses**: Handle edge cases
- **Quick to implement**: Few hours of work
