import datetime

from collections import namedtuple
from django.template import defaultfilters

KeyTest = namedtuple('KeyTest', 'test_id,description,url')


KEY_TESTS = (
    KeyTest(
        test_id='openpgp_v4',
        description='Key uses OpenPGP version 4 format',
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#make-sure-your-key-is-openpgpv4',  # noqa
    ),
    KeyTest(
        test_id='acceptable_primary_key_strength',
        description='Primary key uses acceptable encryption strength',
        url='https://infosec.mozilla.org/guidelines/key_management.html#acceptable---generally-valid-for-up-2-years',  # noqa
    ),
    KeyTest(
        test_id='recommended_primary_key_strength',
        description='Primary key uses recommended encryption strength',
        url='https://infosec.mozilla.org/guidelines/key_management.html#recommended---generally-valid-for-up-to-10-years-default'  # noqa
    ),
    KeyTest(
        test_id='primary_key_expires_within_two_years',
        description='Primary key expires within 2 years from now',
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#use-an-expiration-date-less-than-two-years',  # noqa
    ),
    KeyTest(
        test_id='primary_key_not_expired',
        description='Primary key is within its expiry date',
        url=None,
    ),
    KeyTest(
        test_id='valid_encryption_subkey',
        description="There's a valid, in-date subkey that can be used for encryption",  # noqa
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#have-a-separate-subkey-for-signing',  # noqa
    ),
    KeyTest(
        test_id='valid_signing_subkey',
        description="There's a valid, in-date subkey that can be used for signing",  # noqa
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#have-a-separate-subkey-for-signing',  # noqa
    ),
    KeyTest(
        test_id='has_valid_uid',
        description='The key has a valid, in-date user identifier (UID)',
        url=None,
    ),
    KeyTest(
        test_id='self_sigs_not_md5',
        description='Self signatures should not use MD5',
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#self-signatures-should-not-use-md5-exclusively',  # noqa
    ),
    KeyTest(
        test_id='self_sigs_not_sha1',
        description='Self signatures should not use SHA1',
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#self-signatures-should-not-use-sha1',  # noqa
    ),
    KeyTest(
        test_id='strong_digest_prefs',
        description='Digest preferences should specify strong algorithms first',  # noqa
        url='https://riseup.net/en/security/message-security/openpgp/best-practices/#stated-digest-algorithm-preferences-must-include-at-least-one-member-of-the-sha-2-family-at-a-higher-priority-than-both-md5-and-sha1',  # noqa
    ),
    KeyTest(
        test_id='strong_cipher_prefs',
        description='Cipher preferences should specify strong algorithms first',  # noqa
        url=None,
    ),
)


class Alert():
    def __init__(self, severity, text):
        assert severity in ('danger', 'warning')

        self.severity = severity
        self.text = text

    def __str__(self):
        return self.text

    def _json(self):
        return {
            'severity': self.severity,
            'text': self.text,
        }


def run_tests_task(ascii_key, test_result):
    from .sync_key import parse_ascii_armored_key

    parsed = parse_ascii_armored_key(ascii_key.encode('ascii'))

    test_result.set_test_result(
        'openpgp_v4',
        all(v == 4 for v in parsed['openpgp_versions'])
    )

    test_result.set_test_result(
        'acceptable_primary_key_strength',
        is_acceptable_primary_key_strength(parsed)
    )

    test_result.set_test_result(
        'recommended_primary_key_strength',
        is_recommended_primary_key_strength(parsed)
    )

    test_result.set_test_result(
        'primary_key_expires_within_two_years',
        primary_key_expires_within_two_years(parsed)
    )

    test_result.set_test_result(
        'primary_key_not_expired',
        primary_key_not_expired(parsed)
    )

    test_result.set_test_result(
        'valid_encryption_subkey',
        valid_encryption_subkey(parsed)
    )

    test_result.set_test_result(
        'valid_signing_subkey',
        valid_signing_subkey(parsed)
    )

    test_result.set_test_result(
        'has_valid_uid',
        has_valid_uid(parsed)
    )

    test_result.set_test_result(
        'self_sigs_not_md5',
        self_sigs_not_md5(parsed)
    )

    test_result.set_test_result(
        'self_sigs_not_sha1',
        self_sigs_not_sha1(parsed)
    )

    test_result.set_test_result(
        'strong_digest_prefs',
        strong_digest_prefs(parsed)
    )

    test_result.set_test_result(
        'strong_cipher_prefs',
        strong_cipher_prefs(parsed)
    )


def is_acceptable_primary_key_strength(parsed):
    # https://infosec.mozilla.org/guidelines/key_management.html

    if parsed['algorithm'] == 'RSA':
        return parsed['length_bits'] >= 3072


def is_recommended_primary_key_strength(parsed):
    # https://infosec.mozilla.org/guidelines/key_management.html

    if parsed['algorithm'] == 'RSA':
        return parsed['length_bits'] >= 4096


def primary_key_expires_within_two_years(parsed):
    expiry_date = parsed.get('expiry_date', None)

    if expiry_date:
        two_years_away = datetime.timedelta(days=365 * 2)
        return expiry_date < datetime.date.today() + two_years_away
    else:
        return False


def primary_key_not_expired(parsed):
    return _not_expired(parsed)


def separate_signing_subkey(parsed):
    return None


def _not_expired(subkey):
    if not subkey.get('expiry_date'):
        return True
    return datetime.date.today() < subkey['expiry_date']


def _subkey_valid(subkey):
    return not subkey['revoked'] and _not_expired(subkey)


def valid_encryption_subkey(parsed):
    valid_subkeys = filter(_subkey_valid, parsed['subkeys'])

    def supports_encryption(subkey):
        return 'E' in subkey['capabilities']

    return len(list(filter(supports_encryption, valid_subkeys))) > 0


def valid_signing_subkey(parsed):
    valid_subkeys = filter(_subkey_valid, parsed['subkeys'])

    def supports_signing(subkey):
        return 'S' in subkey['capabilities']

    return len(list(filter(supports_signing, valid_subkeys))) > 0


def has_valid_uid(parsed):
    return len(parsed.get('uids', [])) > 0


def self_sigs_not_md5(parsed):
    return None


def self_sigs_not_sha1(parsed):
    return None


def strong_digest_prefs(parsed):
    """
    We want to see 10, 9, 8, 11 before 3, 2, 1

    https://tools.ietf.org/html/rfc4880#section-9.4
    """
    prefs = parsed.get('digest_preferences')
    if not prefs:
        return None

    return prefs[0] in [11, 10, 9, 8]  # TODO: more sophisticated?


def strong_cipher_prefs(parsed):
    """
    We want to see 9, 8, 7, 3 before ... anything

    https://tools.ietf.org/html/rfc4880#section-9.2
    """
    prefs = parsed.get('cipher_preferences')
    if not prefs:
        return None

    return prefs[0] in [9, 8, 7]  # TODO: more sophisticated?


def make_alerts(pgp_key):
    """
    Return a list of Alert objects for the given PGPKey
    """
    alerts = []

    if pgp_key.revoked:
        alerts.append(make_primary_key_revoked_alert(pgp_key))

    else:
        alerts.append(make_primary_key_expiry_alert(pgp_key))

    return list(filter(None, alerts))


def make_primary_key_expiry_alert(pgp_key):
    if pgp_key.expiry_date is None:
        return Alert('warning', "Primary key doesn't have an expiry date set")

    days_till_expiry = pgp_key.days_till_expiry
    friendly_date = defaultfilters.date(pgp_key.expiry_date, 'DATE_FORMAT')

    if 3 < days_till_expiry <= 30:
        return Alert('warning', 'Primary key expires in {} days'.format(
            days_till_expiry))

    elif 1 < days_till_expiry <= 3:
        return Alert('danger', 'Primary key expires on {} ({} days)'.format(
            friendly_date, days_till_expiry))

    elif days_till_expiry == 1:
        return Alert('danger', 'Primary key expires tomorrow, {}'.format(
            friendly_date))

    elif days_till_expiry == 0:
        return Alert('danger', 'Primary key expired today, {}'.format(
            friendly_date))

    elif days_till_expiry < 0:
        return Alert('danger', 'Primary key expired {} days ago'.format(
            -days_till_expiry))


def make_primary_key_revoked_alert(pgp_key):
    if pgp_key.revoked:
        return Alert(
            'danger',
            'Primary key has been revoked and should no longer be used'
        )
