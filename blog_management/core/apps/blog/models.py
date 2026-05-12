from django.db import models

# Create your models here.
import uuid
from base.models import TimeStampedModel          
from django.conf import settings

class Blog(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image_url = models.URLField(max_length=500, null=True, blank=True)
    object_key = models.CharField(max_length=255, null=True, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title

