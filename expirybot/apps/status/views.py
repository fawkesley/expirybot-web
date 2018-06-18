import datetime
from datetime import timedelta

from django.views.generic import TemplateView
from django.utils import timezone

from expirybot.apps.keys.models import BrokenKey, KeyUpdate, PGPKey
from .models import EventLatestOccurrence


class StatusView(TemplateView):
    template_name = 'status/status.html'

    def get(self, request):
        num_keys = PGPKey.objects.all().count()
        num_broken_keys = BrokenKey.objects.all().count()

        test_results = run_tests()

        all_pass = all(x['pass'] for x in test_results)
        status = 200 if all_pass else 500

        return self.render_to_response({
            'num_keys': num_keys,
            'num_broken_keys': num_broken_keys,
            'tests': run_tests(),
            'daily_histogram': make_daily_histogram(),
        }, status=status)


def make_daily_histogram():
    days = []

    for date in last_30_days():
        day_key_updates = KeyUpdate.objects.filter(updated_at__date=date)

        num_updates = day_key_updates.count()
        num_full = day_key_updates.filter(fingerprint__isnull=False).count()

        if num_updates:
            percent_full = '{:.1f}%'.format(
                100 * (num_full / num_updates)
            )
        else:
            percent_full = '-'

        days.append({
            'date': date,
            'num_updates': num_updates,
            'num_full': num_full,
            'percent_full': percent_full,
        })

    return days


def last_30_days():
    today_midday = datetime.datetime.now().replace(hour=12, minute=0)

    for i in range(30):
        day = (today_midday - datetime.timedelta(hours=i * 24)).date()
        yield day


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
