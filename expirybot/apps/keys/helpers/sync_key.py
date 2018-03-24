import datetime
import logging
import tempfile

import requests

from django.db import transaction
from django.conf import settings
from django.utils import timezone

from expirybot.libs.gpg_wrapper import (
    parse_public_key, GPGError, GPGFatalProblemWithKey
)

from .alerts import make_alerts
from .exceptions import NoSuchKeyError, KeyParsingError

LOG = logging.getLogger(__name__)


def sync_key(key, ascii_key=None):
    """
    Parse an ASCII-armored key, update the given `key` and save it back to the
    database.

    - `ascii_key` should be the OpenPGP ascii armored key, in binary. If not
                  given, the latest key is fetched from the keyserver
    """
    if should_ignore_broken_key(key.fingerprint):
        raise KeyParsingError('Key marked as broken, not syncing.')

    LOG.info('syncing {}'.format(key))

    ascii_key_binary = ascii_key or download_ascii_armored_key(key.key_id)

    assert isinstance(ascii_key_binary, bytes), type(ascii_key_binary)

    try:
        parsed = parse_ascii_armored_key(ascii_key_binary)

    except GPGError as e:
        LOG.exception(e)
        raise KeyParsingError

    except GPGFatalProblemWithKey as e:
        LOG.exception(e)
        record_broken_key(key.fingerprint, repr(e))
        raise KeyParsingError

    with transaction.atomic():
        sync_key_from_parsed(key, parsed)
        key.save()


def should_ignore_broken_key(fingerprint):
    from expirybot.apps.keys.models import BrokenKey

    try:
        key = BrokenKey.objects.get(fingerprint=fingerprint)

    except BrokenKey.DoesNotExist:
        result = False

    else:
        now = timezone.now()
        result = now < key.next_retry_sync

        if result:
            LOG.info('Key {} marked as broken, ignoring until {}'.format(
                fingerprint, key.next_retry_sync)
            )

    return result


def record_broken_key(fingerprint, error_message):
    from expirybot.apps.keys.models import BrokenKey

    one_week = timezone.now() + datetime.timedelta(days=7)

    BrokenKey.objects.update_or_create(
        fingerprint=fingerprint,
        defaults={
            'next_retry_sync': one_week,
            'error_message': error_message,
        }
    )


def download_ascii_armored_key(key_id):
    """
    Fetch the ASCII-armored key from the keyserver and return it as bytes.
    """

    url = '{keyserver}/pks/lookup?op=get&options=mr&search={key_id}'.format(
        keyserver=settings.KEYSERVER_URL, key_id=key_id)

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.HTTPError:
        if response.status_code == 404:
            raise NoSuchKeyError("Keyserver HTTP404 for key {}".format(key_id))
        else:
            raise

    return response.content


def parse_ascii_armored_key(ascii_key_binary):
    with tempfile.NamedTemporaryFile('wb') as f:
        f.write(ascii_key_binary)
        f.flush()

        return parse_public_key(f.name)


def sync_key_from_parsed(key, parsed):
    sync_key_algorithm(key, parsed['algorithm'])
    sync_key_length_bits(key, parsed['length_bits'])
    sync_key_ecc_curve(key, parsed['ecc_curve'])
    sync_key_uids(key, parsed['uids'])
    sync_subkeys(key, translate_subkeys(parsed['subkeys']))
    sync_created_date(key, parsed['created_date'])
    sync_expiry_date(key, parsed['expiry_date'])
    sync_capabilities(key, parsed['capabilities'])
    sync_revoked(key, parsed['revoked'])
    sync_alerts(key, make_alerts(key))
    update_last_synced(key)


def translate_subkeys(parser_subkeys):
    # TODO: think about how to remove this, it's kind of stupid

    def translate(s):
        return {
            'long_id': s['long_id'],
            'key_algorithm': s['algorithm'],
            'key_length_bits': s['length_bits'],
            'ecc_curve': s['ecc_curve'] or '',  # translate None -> ''
            'creation_date': s['created_date'],
            'expiry_date': s['expiry_date'],
            'revoked': s['revoked'],
            'capabilities': s['capabilities'],
        }

    return [translate(s) for s in parser_subkeys]


def sync_key_algorithm(key, algorithm):
    from expirybot.apps.keys.models import CryptographicKey
    allowed_algorithms = [x[0] for x in CryptographicKey.ALGORITHM_CHOICES]

    assert algorithm in allowed_algorithms, \
        'algorithm {} not in {}'.format(algorithm, allowed_algorithms)

    if not key.key_algorithm:
        key.key_algorithm = algorithm
    else:
        assert key.key_algorithm == algorithm, \
            'key.key_algorithm `{}` != algorithm `{}`'.format(
                key.key_algorithm, algorithm)


def sync_key_length_bits(key, length_bits):
    key.key_length_bits = length_bits


def sync_key_ecc_curve(key, ecc_curve):
    if ecc_curve is None:
        ecc_curve = ''

    key.ecc_curve = ecc_curve


def sync_key_uids(key, expected_uids):
    from expirybot.apps.keys.models import UID

    current_uids = [u.uid_string for u in key.uids.all()]

    if current_uids != expected_uids:
        LOG.info('Updating UIDs for {}'.format(key))

        with transaction.atomic():
            key.uids.all().delete()

            for uid_string in expected_uids:
                LOG.debug(uid_string)
                UID.objects.create(key=key, uid_string=uid_string)


def sync_subkeys(key, expected_subkeys):
    from expirybot.apps.keys.models import Subkey

    current_subkeys = [s.to_dict() for s in key.subkeys.all()]

    if current_subkeys != expected_subkeys:
        if len(current_subkeys):
            LOG.info('Deleting & re-creating subkeys for {}: '
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


def sync_alerts(key, alerts):
    key.alerts = alerts


def update_last_synced(key):
    key.last_synced = timezone.now()
