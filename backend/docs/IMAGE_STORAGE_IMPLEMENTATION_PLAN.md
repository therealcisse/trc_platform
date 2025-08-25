# Image Storage Implementation Plan

## Executive Summary
This document outlines the implementation plan for adding the ability to save request images in the database, linked to RequestLog entries, when an environment variable is enabled. This feature will be used to study image endpoint performance.

## Objectives
- Store incoming images for performance analysis
- Link images to existing RequestLog entries
- Make feature optional via environment variable
- Minimize performance impact on production

## Architecture Overview

### Current State
- Images are received at `/api/core/solve` endpoint
- Images are processed and sent to OpenAI
- RequestLog tracks metadata (size, duration, status)
- Images are not persisted

### Proposed State
- When `SAVE_REQUEST_IMAGES=true`, images will be saved
- New `RequestImage` model stores image data
- One-to-one relationship with RequestLog
- Performance metrics can be analyzed with actual image data

## Implementation Details

### 1. Database Model (usage/models.py)

```python
import hashlib
from PIL import Image
import io

class RequestImage(models.Model):
    """Stores image data for requests when SAVE_REQUEST_IMAGES is enabled."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_log = models.OneToOneField(
        'RequestLog', 
        on_delete=models.CASCADE, 
        related_name='saved_image'
    )
    image_data = models.BinaryField()  # Raw image bytes
    mime_type = models.CharField(max_length=50, default='image/jpeg')
    file_size = models.IntegerField()  # Size in bytes
    image_hash = models.CharField(max_length=64, db_index=True)  # SHA256 for deduplication
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'request_images'
        indexes = [
            models.Index(fields=['image_hash']),
            models.Index(fields=['created_at']),
            models.Index(fields=['request_log']),
        ]
    
    def __str__(self):
        return f"Image for request {self.request_log.request_id}"
    
    @classmethod
    def create_from_bytes(cls, request_log, image_bytes, mime_type='image/jpeg'):
        """Create RequestImage from raw bytes with metadata extraction."""
        # Calculate hash for deduplication
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        
        # Extract image dimensions if possible
        width, height = None, None
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
        except Exception:
            pass  # If we can't read the image, just skip dimensions
        
        return cls.objects.create(
            request_log=request_log,
            image_data=image_bytes,
            mime_type=mime_type,
            file_size=len(image_bytes),
            image_hash=image_hash,
            width=width,
            height=height
        )
```

### 2. Settings Configuration (config/settings.py)

```python
# Image storage settings
SAVE_REQUEST_IMAGES = os.environ.get("SAVE_REQUEST_IMAGES", "false").lower() == "true"
# Optional: Maximum image size to save (in MB)
MAX_SAVED_IMAGE_SIZE_MB = int(os.environ.get("MAX_SAVED_IMAGE_SIZE_MB", "10"))
# Optional: Image retention period in days
IMAGE_RETENTION_DAYS = int(os.environ.get("IMAGE_RETENTION_DAYS", "30"))
```

### 3. Update View Logic (core/views.py)

```python
from django.conf import settings
from usage.models import RequestLog, RequestImage

class SolveView(APIView):
    # ... existing code ...
    
    def post(self, request: Request) -> Response:
        # ... existing image extraction code ...
        
        try:
            result = openai_client.solve_image(
                image_bytes, model=settings.openai_model, timeout=settings.openai_timeout_s
            )
            
            # ... existing duration calculation ...
            
            # Create RequestLog as before
            request_log = RequestLog.objects.create(
                user=request.user,
                token=getattr(request, "token", None),
                billing_period=billing_period,
                service="core.image_solve",
                duration_ms=duration_ms,
                request_bytes=len(image_bytes),
                response_bytes=len(result["result"]),
                status="success",
                request_id=request.request_id,
            )
            
            # NEW: Save image if feature is enabled
            if settings.SAVE_REQUEST_IMAGES:
                # Check size limit
                max_size_bytes = settings.MAX_SAVED_IMAGE_SIZE_MB * 1024 * 1024
                if len(image_bytes) <= max_size_bytes:
                    try:
                        # Detect MIME type from request
                        mime_type = 'image/jpeg'  # Default
                        if "file" in request.FILES:
                            mime_type = request.FILES["file"].content_type or mime_type
                        
                        RequestImage.create_from_bytes(
                            request_log=request_log,
                            image_bytes=image_bytes,
                            mime_type=mime_type
                        )
                    except Exception as e:
                        # Log error but don't fail the request
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Failed to save image for request {request.request_id}: {e}")
            
            # ... rest of existing code ...
```

### 4. Database Migration

```python
# usage/migrations/0003_requestimage.py
from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('usage', '0002_billingperiod_requestlog_billing_period_and_more'),
    ]
    
    operations = [
        migrations.CreateModel(
            name='RequestImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('image_data', models.BinaryField()),
                ('mime_type', models.CharField(default='image/jpeg', max_length=50)),
                ('file_size', models.IntegerField()),
                ('image_hash', models.CharField(db_index=True, max_length=64)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('request_log', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='saved_image',
                    to='usage.requestlog'
                )),
            ],
            options={
                'db_table': 'request_images',
            },
        ),
        migrations.AddIndex(
            model_name='requestimage',
            index=models.Index(fields=['image_hash'], name='request_ima_image_h_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='requestimage',
            index=models.Index(fields=['created_at'], name='request_ima_created_654321_idx'),
        ),
    ]
```

### 5. Admin Interface (usage/admin.py)

```python
from django.contrib import admin
from django.utils.html import format_html
from .models import RequestLog, BillingPeriod, RequestImage

# ... existing admin classes ...

@admin.register(RequestImage)
class RequestImageAdmin(admin.ModelAdmin):
    list_display = ['request_log_id', 'file_size_display', 'dimensions', 'mime_type', 'created_at']
    list_filter = ['mime_type', 'created_at']
    search_fields = ['request_log__request_id', 'image_hash']
    readonly_fields = ['id', 'image_preview', 'image_hash', 'file_size', 'width', 'height', 'created_at']
    
    def request_log_id(self, obj):
        return obj.request_log.request_id
    request_log_id.short_description = 'Request ID'
    
    def file_size_display(self, obj):
        # Convert bytes to human-readable format
        size = obj.file_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} GB"
    file_size_display.short_description = 'Size'
    
    def dimensions(self, obj):
        if obj.width and obj.height:
            return f"{obj.width}x{obj.height}"
        return "Unknown"
    dimensions.short_description = 'Dimensions'
    
    def image_preview(self, obj):
        # Show small preview in admin
        import base64
        if obj.image_data:
            b64_image = base64.b64encode(obj.image_data).decode('utf-8')
            return format_html(
                '<img src="data:{};base64,{}" style="max-width: 200px; max-height: 200px;" />',
                obj.mime_type,
                b64_image
            )
        return "No image"
    image_preview.short_description = 'Preview'
```

### 6. Data Retention Management Command

```python
# usage/management/commands/cleanup_old_images.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from usage.models import RequestImage

class Command(BaseCommand):
    help = 'Clean up old saved images based on retention policy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=settings.IMAGE_RETENTION_DAYS,
            help='Number of days to retain images'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_images = RequestImage.objects.filter(created_at__lt=cutoff_date)
        count = old_images.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No old images to delete'))
            return
        
        if dry_run:
            self.stdout.write(f'Would delete {count} images older than {days} days')
        else:
            old_images.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} old images'))
```

### 7. Performance Analysis Views

```python
# usage/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum
from .models import RequestLog, RequestImage

@api_view(['GET'])
@permission_classes([IsAdminUser])
def image_performance_stats(request):
    """Get performance statistics for saved images."""
    
    # Get requests with saved images
    requests_with_images = RequestLog.objects.filter(
        saved_image__isnull=False
    ).select_related('saved_image')
    
    stats = requests_with_images.aggregate(
        total_requests=Count('id'),
        avg_duration_ms=Avg('duration_ms'),
        avg_image_size=Avg('saved_image__file_size'),
        total_storage_bytes=Sum('saved_image__file_size'),
    )
    
    # Group by image dimensions
    dimension_stats = requests_with_images.values(
        'saved_image__width', 
        'saved_image__height'
    ).annotate(
        count=Count('id'),
        avg_duration=Avg('duration_ms'),
        avg_size=Avg('saved_image__file_size')
    ).order_by('-count')[:10]
    
    return Response({
        'overall_stats': stats,
        'by_dimensions': dimension_stats,
        'storage_used_mb': (stats['total_storage_bytes'] or 0) / (1024 * 1024),
    })
```

## Testing Strategy

### Unit Tests
```python
# usage/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import RequestLog, RequestImage
import hashlib

class RequestImageTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass'
        )
        self.request_log = RequestLog.objects.create(
            user=self.user,
            service='core.image_solve',
            duration_ms=100,
            request_bytes=1000,
            response_bytes=50,
            status='success',
            request_id='test-request-id'
        )
    
    def test_create_from_bytes(self):
        image_bytes = b'fake image data'
        image = RequestImage.create_from_bytes(
            request_log=self.request_log,
            image_bytes=image_bytes,
            mime_type='image/png'
        )
        
        self.assertEqual(image.file_size, len(image_bytes))
        self.assertEqual(image.mime_type, 'image/png')
        self.assertEqual(
            image.image_hash, 
            hashlib.sha256(image_bytes).hexdigest()
        )
    
    @patch('django.conf.settings.SAVE_REQUEST_IMAGES', True)
    def test_image_saved_when_enabled(self):
        # Test that image is saved when feature is enabled
        pass
    
    @patch('django.conf.settings.SAVE_REQUEST_IMAGES', False)
    def test_image_not_saved_when_disabled(self):
        # Test that image is not saved when feature is disabled
        pass
```

## Deployment Steps

1. **Add environment variables**:
   ```bash
   SAVE_REQUEST_IMAGES=false  # Start disabled
   MAX_SAVED_IMAGE_SIZE_MB=10
   IMAGE_RETENTION_DAYS=30
   ```

2. **Run migrations**:
   ```bash
   uv run python manage.py makemigrations
   uv run python manage.py migrate
   ```

3. **Test in staging**:
   - Enable feature with `SAVE_REQUEST_IMAGES=true`
   - Send test requests
   - Verify images are saved
   - Check admin interface

4. **Setup cron job for cleanup**:
   ```bash
   # Run daily at 2 AM
   0 2 * * * cd /app && uv run python manage.py cleanup_old_images
   ```

5. **Monitor performance**:
   - Database size growth
   - Query performance
   - Storage usage

## Performance Metrics to Track

1. **Storage Metrics**:
   - Total storage used
   - Average image size
   - Image count by dimension

2. **Performance Metrics**:
   - Processing time by image size
   - Processing time by image dimensions
   - Error rate by image characteristics

3. **Usage Patterns**:
   - Most common image dimensions
   - Peak usage times
   - User-specific patterns

## Security Considerations

1. **Access Control**:
   - Only admins can view saved images
   - Images linked to user accounts
   - Audit trail via RequestLog

2. **Data Privacy**:
   - Images contain user-submitted content
   - Consider encryption at rest
   - Implement proper data retention

3. **Storage Limits**:
   - Enforce maximum image size
   - Implement retention policy
   - Monitor for abuse

## Future Enhancements

1. **Deduplication**:
   - Use image_hash to avoid storing duplicates
   - Reference counting for shared images

2. **Compression**:
   - Compress images before storage
   - Use efficient formats (WebP)

3. **External Storage**:
   - Move to S3/GCS for large scale
   - CDN integration for serving

4. **Analytics Dashboard**:
   - Visual performance metrics
   - Image processing trends
   - Error analysis by image type

## Rollback Plan

If issues arise:

1. **Disable feature**:
   ```bash
   SAVE_REQUEST_IMAGES=false
   ```

2. **Clean up data** (if needed):
   ```sql
   TRUNCATE TABLE request_images;
   ```

3. **Revert migration** (last resort):
   ```bash
   uv run python manage.py migrate usage 0002
   ```

## Conclusion

This implementation provides a robust, optional image storage system linked to RequestLog entries for performance analysis. The feature is designed to be:
- **Optional**: Controlled by environment variable
- **Performant**: Minimal impact on request processing
- **Maintainable**: Clear separation of concerns
- **Scalable**: Can handle growth with proper retention

The implementation prioritizes simplicity and reliability while providing valuable data for performance analysis.
