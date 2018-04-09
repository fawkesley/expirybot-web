import datetime
import logging


from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from expirybot.apps.users.models import UserProfile

from expirybot.apps.users.email_helpers import send_welcome_email
from expirybot.apps.users.utils import make_authenticated_one_click_config_url

from expirybot.apps.status.models import EventLatestOccurrence


LOG = logging.getLogger(__name__)

SEARCH_PERIOD = datetime.timedelta(hours=1)


class Command(BaseCommand):
    help = ('Monitors whether PGP keys have been added for a given email.')

    def handle(self, *args, **options):
        send_welcome_emails()


def send_welcome_emails():

    twenty_four_hours_ago = timezone.now() - datetime.timedelta(hours=24)

    new_user_profiles = UserProfile.objects.filter(
        created_at__lte=twenty_four_hours_ago,
        user__username__startswith='auto-',
        user__email__isnull=False,
        welcome_email_sent_datetime=None,
        ).order_by('-created_at')[0:3]

    LOG.info('Emailing {} new users'.format(new_user_profiles.count()))

    for profile in new_user_profiles:
        send_welcome_email_for_profile(profile)


def send_welcome_email_for_profile(profile):

    enable_feedback_url = make_authenticated_one_click_config_url(
        profile,
        'receive_occasional_feedback_requests',
        True
    )

    try:
        with transaction.atomic():
            profile.welcome_email_sent_datetime = timezone.now()
            profile.save()
            send_welcome_email(profile.user.email, enable_feedback_url)

    except Exception as e:
        LOG.exception(e)

    else:
        EventLatestOccurrence.record_event('sent-welcome-email')
