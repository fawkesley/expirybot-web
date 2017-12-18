import logging
import tempfile
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from expirybot.apps.keys.models import (
    PGPKey, UID
)

from expirybot.libs.gpg_wrapper import parse_public_key, GPGError

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

    LOG.info("All done.")


def get_keys_never_synced():
    return PGPKey.objects.filter(last_synced=None)


def sync_key(key):
    print('syncing {}'.format(key))

    response = requests.get('https://keyserver.paulfurley.com/pks/lookup?op=get&options=mr&search={}'.format(key.key_id))
    response.raise_for_status()

    with tempfile.NamedTemporaryFile('wb') as f:
        f.write(response.content)
        f.flush()

        try:
            parsed = parse_public_key(f.name)
        except GPGError as e:
            LOG.exception(e)
            return

        assert parsed['fingerprint'] == key.fingerprint

    with transaction.atomic():
        sync_key_uids(key, parsed['uids'])
        sync_created_date(key, parsed['created_date'])
        sync_expiry_date(key, parsed['expiry_date'])
        update_last_synced(key)
        key.save()


def sync_key_uids(key, expected_uids):

    current_uids = [u.uid_string for u in key.uids.all()]

    if current_uids != expected_uids:
        print('Updating UIDs for {}'.format(key))

        with transaction.atomic():
            key.uids.all().delete()

            for uid_string in expected_uids:
                print(uid_string)
                UID.objects.create(key=key, uid_string=uid_string)


def sync_created_date(key, date):
    key.creation_datetime = date


def sync_expiry_date(key, date):
    key.expiry_datetime = date


def update_last_synced(key):
    key.last_synced = timezone.now()
