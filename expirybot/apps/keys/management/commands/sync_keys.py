import logging

from django.core.management.base import BaseCommand

from expirybot.apps.keys.helpers import sync_key

from expirybot.apps.keys.models import PGPKey

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
    for key in get_keys_never_synced():
        sync_key(key)

    LOG.info("sync_keys finished.")


def get_keys_never_synced():
    return PGPKey.objects.filter(last_synced=None)
