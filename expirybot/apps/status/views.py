from datetime import timedelta

from django.views.generic import TemplateView
from django.utils import timezone

from expirybot.apps.keys.models import BrokenKey, PGPKey
from .models import EventLatestOccurrence


class StatusView(TemplateView):
    template_name = 'status/status.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        num_keys = PGPKey.objects.all().count()
        num_broken_keys = BrokenKey.objects.all().count()

        ctx.update({
            'num_keys': num_keys,
            'num_broken_keys': num_broken_keys,
            'tests': run_tests(),
        })
        return ctx


def run_tests():
    return [
        {
            'slug': 'expirybot-requested-unsubscribe-urls-recently',
            'pass': _check_event_occurred_within(
                'api-call-unsubscribe-url', timedelta(hours=24)
            ),
        },
        {
            'slug': 'monitor-email-addresses-ran-recently',
            'pass': _check_event_occurred_within(
                'monitor-email-addresses-succeeded', timedelta(minutes=5)
            ),
        },
        {
            'slug': 'sync-keys-ran-recently',
            'pass': _check_event_occurred_within(
                'sync-keys-succeeded', timedelta(hours=1)
            ),
        },
        {
            'slug': 'sync-mailgun-suppressions-ran-recently',
            'pass': _check_event_occurred_within(
                'sync-mailgun-suppressions-succeeded', timedelta(hours=2)
            ),
        },
        {
            'slug': 'sync-mailgun-no-mx-domains-ran-recently',
            'pass': _check_event_occurred_within(
                'sync-mailgun-no-mx-domains-succeeded', timedelta(hours=26)
            ),
        },
        {
            'slug': 'delete-old-test-results-ran-recently',
            'pass': _check_event_occurred_within(
                'delete-old-test-results-succeeded', timedelta(hours=2)
            ),
        },
    ]


def _check_event_occurred_within(event_slug, max_delta):
    try:
        occurrence = EventLatestOccurrence.objects.get(event_slug=event_slug)
    except EventLatestOccurrence.DoesNotExist:
        return False

    now = timezone.now()
    delta = now - occurrence.last_occurred_datetime
    return delta < max_delta
