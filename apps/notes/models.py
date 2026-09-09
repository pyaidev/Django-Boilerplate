from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from apps.common.models import BaseModel


class Note(BaseModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, max_length=20000)
    is_archived = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["owner", "-created_at"], name="note_owner_created_idx")]

    def __str__(self):
        return self.title
