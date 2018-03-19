from django.db import models
from django.utils import timezone


class EventLatestOccurrence(models.Model):

    @staticmethod
    def record_event(event_slug):
        now = timezone.now()

        EventLatestOccurrence.objects.update_or_create(
            event_slug=event_slug,
            defaults={'last_occurred_datetime': now}
        )

    event_slug = models.CharField(
        primary_key=True,
        max_length=100
    )

    last_occurred_datetime = models.DateTimeField(null=False, blank=False)
