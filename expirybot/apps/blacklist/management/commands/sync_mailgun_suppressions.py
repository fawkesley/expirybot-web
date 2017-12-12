import datetime
import logging
import requests


from django.core.management.base import BaseCommand
# from django.db import transaction
from django.conf import settings
from django.utils import timezone

from expirybot.apps.blacklist.models import EmailAddress

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ('Updates keys from the keyserver')

    def handle(self, *args, **options):
        sync_mailgun_suppressions()


def sync_mailgun_suppressions():
    for (email, unsubscribe_datetime) in get_unsubscribes():
        record_unsubscribe(email, unsubscribe_datetime)

    for (email, complain_datetime) in get_complaints():
        record_complaint(email, complain_datetime)

    for (email, bounce_datetime) in get_bounces():
        record_bounce(email, bounce_datetime)


def get_unsubscribes():
    return get_suppression('unsubscribes')


def get_complaints():
    return get_suppression('complaints')


def get_bounces():
    return get_suppression('bounces')


def get_suppression(type_):
    mailgun_domain = 'keyserver.paulfurley.com'

    api_key = settings.MAILGUN_API_KEY
    if not api_key:
        raise RuntimeError('Bad Mailgun API key: {}'.format(api_key))

    response = requests.get(
        'https://api.mailgun.net/v3/{domain}/{type_}'.format(
            domain=mailgun_domain, type_=type_
        ),
        auth=('api', api_key),
    )

    response.raise_for_status()

    for item in response.json()['items']:
        email = item['address']
        created_at = parse_mailgun_date(item['created_at'])

        yield email, created_at


def parse_mailgun_date(string):
    """
    Example: Tue, 15 Aug 2017 14:27:09 UTC
    """

    fmt = '%a, %d %b %Y %H:%M:%S UTC'
    return datetime.datetime.strptime(string, fmt).replace(tzinfo=timezone.utc)


def record_unsubscribe(email, unsubscribed_at):
    obj, new = EmailAddress.objects.get_or_create(email_address=email)
    LOG.info("unsubscribe {} - {}".format(email, unsubscribed_at))

    if obj.unsubscribe_datetime:
        obj.unsubscribe_datetime = min(
            unsubscribed_at, obj.unsubscribe_datetime
        )
    else:
        obj.unsubscribe_datetime = unsubscribed_at

    obj.save()


def record_complaint(email, complain_datetime):
    obj, new = EmailAddress.objects.get_or_create(email_address=email)
    LOG.info("complain {} - {}".format(email, complain_datetime))

    if obj.complain_datetime:
        obj.complain_datetime = min(
            complain_datetime, obj.complain_datetime
        )
    else:
        obj.complain_datetime = complain_datetime

    obj.save()


def record_bounce(email, bounce_datetime):
    obj, new = EmailAddress.objects.get_or_create(email_address=email)
    LOG.info("bounce {} - {}".format(email, bounce_datetime))

    if obj.last_bounce_datetime:
        obj.last_bounce_datetime = max(
            bounce_datetime, obj.bounce_datetime
        )
    else:
        obj.last_bounce_datetime = bounce_datetime

    obj.save()
