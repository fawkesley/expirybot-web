import logging
import tempfile

import requests

from django.db import transaction
from django.conf import settings
from django.utils import timezone

from expirybot.libs.gpg_wrapper import parse_public_key, GPGError
from expirybot.apps.keys.models import PGPKey, Subkey, UID

from .exceptions import NoSuchKeyError

LOG = logging.getLogger(__name__)


def sync_key(key):
    LOG.info('syncing {}'.format(key))

    url = '{keyserver}/pks/lookup?op=get&options=mr&search={key_id}'.format(
        keyserver=settings.KEYSERVER_URL, key_id=key.key_id)

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.HTTPError:
        if response.status_code == 404:
            raise NoSuchKeyError("Keyserver HTTP 404 for key {}".format(key))
        else:
            raise

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
        sync_subkeys(key, translate_subkeys(parsed['subkeys']))
        sync_created_date(key, parsed['created_date'])
        sync_expiry_date(key, parsed['expiry_date'])
        sync_capabilities(key, parsed['capabilities'])
        sync_revoked(key, parsed['revoked'])
        update_last_synced(key)
        key.save()


def translate_subkeys(parser_subkeys):
    # TODO: think about how to remove this, it's kind of stupid

    def translate(s):
        return {
            'long_id': s['long_id'],
            'key_algorithm': s['algorithm'],
            'key_length_bits': s['length_bits'],
            'creation_date': s['created_date'],
            'expiry_date': s['expiry_date'],
            'revoked': s['revoked'],
            'capabilities': s['capabilities'],
        }

    return [translate(s) for s in parser_subkeys]


def sync_key_algorithm(key, algorithm):
    allowed_algorithms = [x[0] for x in PGPKey.ALGORITHM_CHOICES]

    assert algorithm in allowed_algorithms, \
        'algorithm {} not in {}'.format(algorithm, allowed_algorithms)

    if not key.key_algorithm:
        key.key_algorithm = algorithm
    else:
        assert key.key_algorithm == algorithm, \
            'key.key_algorithm `{}` != algorithm `{}`'.format(
                key.key_algorithm, algorithm)


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


def sync_subkeys(key, expected_subkeys):

    current_subkeys = [s.to_dict() for s in key.subkeys.all()]

    if current_subkeys != expected_subkeys:
        if len(current_subkeys):
            LOG.warn('Deleting & re-creating subkeys for {}: '
                     'current: {} expected: {}'.format(
                         key, current_subkeys, expected_subkeys))
        else:
            LOG.info('Setting key.subkeys: {}'.format(expected_subkeys))

        with transaction.atomic():
            key.subkeys.all().delete()

            for subkey_data in expected_subkeys:
                Subkey.objects.create(key=key, **subkey_data)


def sync_created_date(key, date):
    key.creation_date = date


def sync_expiry_date(key, date):
    key.expiry_date = date


def sync_capabilities(key, capabilities):
    assert isinstance(capabilities, list)
    for capability in capabilities:
        assert capability in ('C', 'S', 'E', 'A')

    if key.capabilities != capabilities:
        key.capabilities = capabilities


def sync_revoked(key, is_revoked):
    assert is_revoked in (True, False)
    key.revoked = is_revoked


def update_last_synced(key):
    key.last_synced = timezone.now()
