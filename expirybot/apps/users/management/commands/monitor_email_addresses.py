import datetime
import re
import logging
import requests


from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from expirybot.apps.users.models import SearchResultForKeysByEmail

from expirybot.apps.users.email_helpers import (
    send_initial_email_monitoring_email, send_new_key_email_monitoring_email
)

from expirybot.apps.blacklist.models import EmailAddress
from expirybot.apps.status.models import EventLatestOccurrence


LOG = logging.getLogger(__name__)

SEARCH_PERIOD = datetime.timedelta(hours=1)


class FailedToGetFingerprintsError(RuntimeError):
    pass


class Command(BaseCommand):
    help = ('Monitors whether PGP keys have been added for a given email.')

    def handle(self, *args, **options):
        monitor_email_addresses()


def monitor_email_addresses():
    email_addresses = EmailAddress.objects.filter(
        owner_proof__isnull=False,
        owner_proof__profile__notify_email_addresses=True
    )

    emails_never_checked = email_addresses.filter(
        latest_search_by_email__isnull=True
    )

    now = timezone.now()
    old = now - SEARCH_PERIOD

    emails_old_check = email_addresses.filter(
        latest_search_by_email__isnull=False,
        latest_search_by_email__datetime__lt=old
    ).order_by('latest_search_by_email__datetime')

    LOG.info(
        '{} emails total, {} emails never checked, {} old checks'.format(
            email_addresses.count(),
            emails_never_checked.count(),
            emails_old_check.count(),
        )
    )

    for email_address in emails_never_checked:
        check_email_address(email_address)

    for email_address in emails_old_check:
        check_email_address(email_address)

    EventLatestOccurrence.record_event('monitor-email-addresses-succeeded')


def check_email_address(email_address):
    LOG.info("Checking keys for {}".format(email_address))

    try:
        fingerprints_now = get_set_of_fingerprints(email_address.email_address)
    except FailedToGetFingerprintsError as e:
        LOG.exception(e)
        return

    try:
        latest = SearchResultForKeysByEmail.objects.get(
            email_address=email_address
        )

    except SearchResultForKeysByEmail.DoesNotExist:
        save_initial_search_result(email_address, fingerprints_now)

    else:
        fingerprints_before = set(latest.key_fingerprints)

        compare_and_save_search_result(
            email_address, fingerprints_before, fingerprints_now, latest
        )


def save_initial_search_result(email_address, fingerprints):
    LOG.info("Saving initial list of keys for {}: {}".format(
        email_address, fingerprints)
    )

    with transaction.atomic():
        SearchResultForKeysByEmail.objects.create(
            email_address=email_address,
            key_fingerprints=list(fingerprints),
        )
        send_initial_email_monitoring_email(
            email_address.email_address, fingerprints
        )


def compare_and_save_search_result(email_address, fingerprints_before,
                                   fingerprints_now, latest_search_result):

    assert isinstance(fingerprints_before, set)
    assert isinstance(fingerprints_now, set)

    keys_added = fingerprints_now - fingerprints_before

    if keys_added:
        LOG.info('keys added: {}'.format(keys_added))

    with transaction.atomic():
        latest_search_result.delete()

        SearchResultForKeysByEmail.objects.create(
            email_address=email_address,
            key_fingerprints=list(fingerprints_now)
        )

        if keys_added:
            # Do this last to rollback transaction on fail
            send_new_key_email_monitoring_email(
                email_address.email_address,
                keys_added
            )


def get_set_of_fingerprints(email_address):
    assert isinstance(email_address, str)

    try:
        response = requests.get(
            '{}/pks/lookup'.format(settings.KEYSERVER_URL),
            params={
                'op': 'vindex',
                'options': 'mr',
                'search': email_address,
            },
            timeout=30
        )
    except requests.ReadTimeout:
        raise FailedToGetFingerprintsError(
            "timeout requesting keys for {}".format(email_address)
        )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        if response.status_code == 404 and 'No keys found' in response.text:
            return set()
        raise

    return set(parse_vindex_for_fingerprints(response.text))


def parse_vindex_for_fingerprints(string):
    fingerprints = []

    for line in string.split('\n'):
        if line.startswith('pub:'):
            (_, fingerprint, _, _, _, _, flags) = line.split(':')
            assert validate_fingerprint(fingerprint), fingerprint

            if flags != 'r':  # revoked
                fingerprints.append(fingerprint)

    return fingerprints


def validate_fingerprint(fingerprint):
    return (
        re.match('^[A-F0-9]{40}$', fingerprint)
        or re.match('^[A-F0-9]{16}$', fingerprint)
    )
