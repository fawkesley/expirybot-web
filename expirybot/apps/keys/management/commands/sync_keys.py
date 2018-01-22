import datetime
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from expirybot.apps.keys.helpers import get_key, sync_key
from expirybot.apps.keys.models import PGPKey

from expirybot.apps.users.models import SearchResultForKeysByEmail

LOG = logging.getLogger(__name__)


ALGOS = {
    1: 'RSA',
    3: 'RSA-SIGN',
    16: 'ELGAMAL',
    17: 'DSA',
    18: 'ECC',
    19: 'ECDSA',
}


class Command(BaseCommand):
    help = ('Updates keys from the keyserver')

    def handle(self, *args, **options):
        sync_keys()


def sync_keys():
    new_fingerprints = get_new_fingerprints_from_search_results()
    keys_never_synced = get_keys_never_synced()
    stale_keys = get_stale_keys()

    LOG.info("{} new fingerprints, {} keys never synced, {} stale keys".format(
        len(new_fingerprints), len(keys_never_synced), len(stale_keys)))

    for fingerprint in new_fingerprints:
        get_key(fingerprint)

    for key in keys_never_synced:
        sync_key(key)

    for key in stale_keys:
        sync_key(key)

    LOG.info("sync_keys finished.")


def get_new_fingerprints_from_search_results():
    """
    Find key fingerprints from SearchResultForKeysByEmail which haven't yet
    been added as PGPKey objects, and add them.
    """

    already_got_fingerprints = set(
        p.fingerprint for p in PGPKey.objects.all()
    )
    found_fingerprints = set()

    for search_result in SearchResultForKeysByEmail.objects.all():
        found_fingerprints.update(search_result.key_fingerprints)

    return found_fingerprints - already_got_fingerprints


def get_keys_never_synced():
    return PGPKey.objects.filter(last_synced=None)


def get_stale_keys():
    one_day_ago = timezone.now() - datetime.timedelta(hours=24)

    return PGPKey.objects.filter(
        last_synced__isnull=False,
        last_synced__lt=one_day_ago
    ).order_by('last_synced')  # ascending: oldest first
