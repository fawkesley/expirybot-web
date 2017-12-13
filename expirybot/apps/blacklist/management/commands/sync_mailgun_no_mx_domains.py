import datetime
import json
import logging
import requests


from django.core.management.base import BaseCommand
# from django.db import transaction
from django.conf import settings
from django.utils import timezone

from expirybot.apps.blacklist.models import BlacklistedDomain

LOG = logging.getLogger(__name__)

mailgun_domain = 'keyserver.paulfurley.com'

# https://tools.ietf.org/html/rfc2822.html#page-14
MAILGUN_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S UTC'

HARDFAILS = (
    'getsockopt: connection refused',
    'getsockopt: no route to host',
    'No MX',
    'i/o timeout',
)


class Command(BaseCommand):
    help = ('Updates keys from the keyserver')

    def handle(self, *args, **options):
        sync_mailgun_suppressions()


def sync_mailgun_suppressions():
    for domain, reason_text in get_no_mx_domains():
        blacklist_domain(domain, reason_text)


def get_no_mx_domains():
    api_key = settings.MAILGUN_API_KEY
    if not api_key:
        raise RuntimeError('Bad Mailgun API key: {}'.format(api_key))

    url = 'https://api.mailgun.net/v3/{domain}/events'.format(
        domain=mailgun_domain
    )

    urls_processed = set()

    for page in range(50):
        response = requests.get(
            url,
            auth=('api', api_key),
            params={
                "begin": (timezone.now() - datetime.timedelta(days=365)).strftime(MAILGUN_DATE_FORMAT),
                "end": timezone.now().strftime(MAILGUN_DATE_FORMAT),
                "limit": 100,
                "pretty": "yes",
                "event": "failed",
                "severity": "permanent",
                "reason": "old",
            }
        )

        try:
            response.raise_for_status()
        except:
            print(response.text)
            raise

        for item in response.json()['items']:
            if any(m in item['delivery-status']['message'] for m in HARDFAILS):
                yield (
                    item['recipient-domain'],
                    json.dumps(item, indent=4)
                )

        urls_processed.add(url)
        url = response.json()['paging']['next']  # Mailgun 'next' loop round :(
        if url in urls_processed:
            break


def parse_mailgun_date(string):
    """
    Example: Tue, 15 Aug 2017 14:27:09 UTC
    """

    return datetime.datetime.strptime(
        string, MAILGUN_DATE_FORMAT
    ).replace(tzinfo=timezone.utc)


def blacklist_domain(domain, reason_text):
    obj, new = BlacklistedDomain.objects.get_or_create(domain=domain)
    LOG.info("blacklist {}".format(domain))

    if obj.comment is None:
        obj.comment = reason_text
        obj.save()
