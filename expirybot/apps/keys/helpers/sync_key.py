import logging
import tempfile

import requests

from django.db import transaction
from django.conf import settings
from django.utils import timezone

from expirybot.libs.gpg_wrapper import parse_public_key, GPGError
from expirybot.apps.keys.models import PGPKey, UID

LOG = logging.getLogger(__name__)


def sync_key(key):
    LOG.info('syncing {}'.format(key))

    url = '{keyserver}/pks/lookup?op=get&options=mr&search={key_id}'.format(
        keyserver=settings.KEYSERVER_URL, key_id=key.key_id)

    response = requests.get(url, timeout=5)
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
        sync_key_algorithm(key, parsed['algorithm'])
        sync_key_length_bits(key, parsed['length_bits'])
        sync_key_uids(key, parsed['uids'])
        sync_created_date(key, parsed['created_date'])
        sync_expiry_date(key, parsed['expiry_date'])
        update_last_synced(key)
        key.save()


def sync_key_algorithm(key, algorithm):
    allowed_algorithms = [x[0] for x in PGPKey.ALGORITHM_CHOICES]

    assert algorithm in allowed_algorithms, \
        'algorithm {} not in {}'.format(algorithm, allowed_algorithms)

    if key.key_algorithm is None:
        key.key_algorithm = algorithm
    else:
        assert key.key_algorithm == algorithm


def sync_key_length_bits(key, length_bits):
    if key.key_length_bits is None:
        key.key_length_bits = length_bits
    else:
        assert key.key_length_bits == length_bits


def sync_key_uids(key, expected_uids):

    current_uids = [u.uid_string for u in key.uids.all()]

    if current_uids != expected_uids:
        LOG.info('Updating UIDs for {}'.format(key))

        with transaction.atomic():
            key.uids.all().delete()

            for uid_string in expected_uids:
                LOG.info(uid_string)
                UID.objects.create(key=key, uid_string=uid_string)


def sync_created_date(key, date):
    key.creation_datetime = date


def sync_expiry_date(key, date):
    key.expiry_datetime = date


def update_last_synced(key):
    key.last_synced = timezone.now()
