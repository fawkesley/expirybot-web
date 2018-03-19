import datetime
import io
import subprocess
import sys
import logging
import re

from os.path import abspath, dirname, join as pjoin
import os

from django.conf import settings

from expirybot.apps.keys.models import CryptographicKey


LOG = logging.getLogger(__name__)

# TODO: Replace gpg2_sandbox with new script/encrypt <public_key> <messgae>
GPG2_SANDBOXED = abspath(pjoin(dirname(__file__), 'gpg2_sandboxed'))
DUMP_KEY = abspath(pjoin(dirname(__file__), 'script', 'dump_key'))

PUB_SUB_PATTERN = r'^(pub|sub)\s+ (?P<algorithm>[A-Za-z0-9]+)\/0x(?P<long_id>[0-9A-F]{16}) (?P<created_date>\d{4}-\d{2}-\d{2}) \[(?P<capabilities>[AECS]*)\]( \[(?P<status>expires|expired|revoked): (?P<status_data>[^ ]+) *\])?$'  # noqa


class GPGError(RuntimeError):
    pass


def parse_public_key(pgp_key_filename):
    list_keys, list_packets = run_dump_key(pgp_key_filename)

    parsed = {}

    parsed.update(parse_list_keys(list_keys))
    parsed.update(parse_list_packets(list_packets))

    return parsed


def run_dump_key(pgp_key_filename):
    dump_key_stdout = stdout_for_subprocess([DUMP_KEY, pgp_key_filename])

    match = re.search('LIST_KEYS: (?P<list_keys>.*)\n'
                      'LIST_PACKETS: (?P<list_packets>.*)\n', dump_key_stdout)

    with io.open(match.group('list_keys'), 'r') as f:
        list_keys = f.read()

    with io.open(match.group('list_packets'), 'r') as f:
        list_packets = f.read()

    return list_keys, list_packets


def encrypt_message(fingerprint, text):
    _receive_key(fingerprint)
    return _encrypt_text(fingerprint, text)


def _receive_key(fingerprint):
    LOG.info('receiving key {}'.format(fingerprint))
    return stdout_for_subprocess([
        GPG2_SANDBOXED,
        '--keyserver',
        settings.KEYSERVER_URL,
        '--recv-key',
        fingerprint
    ])


def _encrypt_text(fingerprint, text):
    LOG.info('encrypting to {}'.format(fingerprint))
    return stdout_for_subprocess([
        GPG2_SANDBOXED,
        '--recipient',
        fingerprint,
        '--comment',
        'Copy & paste this encrypted message into your GPG/PGP software',
        '--no-version',
        '--armor',
        '--trust-model',
        'always',
        '--encrypt',
    ], stdin=text).strip()


def parse_list_keys(stdout):
    result = {
        'fingerprint': _parse_fingerprint_line(stdout),
        'uids': list(_parse_uid_lines(stdout)),
        'subkeys': list(_parse_subkey_lines(stdout)),
    }

    result.update(_parse_pub_line(stdout))

    return result


def parse_list_packets(list_packets):
    return {
        'openpgp_versions': parse_openpgp_versions(list_packets),
        'cipher_preferences': parse_cipher_preferences(list_packets),
        'digest_preferences': parse_digest_preferences(list_packets),
    }


def parse_openpgp_versions(list_packets):
    versions = set()

    for line in list_packets.split('\n'):
        if line.lstrip().startswith('version'):
            versions.add(int(line.lstrip()[8]))

    return list(sorted(versions))


def parse_cipher_preferences(list_packets):
    """
    (pref-sym-algos: 9 8 7 3 2)
    """
    match = re.search('\(pref-sym-algos: (?P<algos>[ 0-9]+)\)', list_packets)
    if match is not None:
        return [int(c) for c in match.group('algos').split(' ')]


def parse_digest_preferences(list_packets):
    """
    (pref-hash-algos: 8 2 9 10 11)
    """
    match = re.search('\(pref-hash-algos: (?P<algos>[ 0-9]+)\)', list_packets)
    if match is not None:
        return [int(c) for c in match.group('algos').split(' ')]


def mkdir_p(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)
    return directory


def save_list_keys_stdout(fingerprint, stdout_text):
    directory = '/tmp/gpg_list_keys/'
    path = pjoin(directory, fingerprint.replace(' ', '') + '.txt')

    mkdir_p(directory)

    with io.open(path, 'w') as f:
        f.write(stdout_text)


def stdout_for_subprocess(cmd_parts, stdin=None):
    LOG.info('Running {}'.format(' '.join(cmd_parts)))
    p = subprocess.Popen(
        cmd_parts,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        if stdin is None:
            stdout, stderr = p.communicate(timeout=5)
        else:
            stdout, stderr = p.communicate(
                input=stdin.encode('utf-8'),
                timeout=5
            )  # closes stdin/stdout

    except subprocess.TimeoutExpired as e:
        p.kill()
        stdout, stderr = p.communicate()
        LOG.exception(e)
        raise GPGError('Command timed out: {} \n{}\n{}'.format(
            p.returncode, stdout, stderr))
    else:
        if p.returncode != 0:
            raise GPGError(
                'failed with code {} stdout: {} stderr: {}'.format(
                    p.returncode, stdout, stderr
                )
            )

    if stdout is None:
        raise GPGError('Got back empty stdout')

    if stderr is None:
        stderr = b''

    LOG.debug(stdout.decode('utf-8'))
    LOG.debug(stderr.decode('utf-8'))

    return stdout.decode('utf-8')


def _parse_fingerprint_line(list_keys_output):
    """
    `      Key fingerprint = A999 B749 8D1A 8DC4 73E5  3C92 309F 635D AD1B 5517`  # noqa
    """

    fingerprints = []

    for line in list_keys_output.split('\n'):
        match = re.match('^\s*Key fingerprint = (?P<fingerprint>.*)$', line)

        if match is not None:
            fingerprints.append(match.group('fingerprint'))

    assert len(fingerprints) == 1, 'expected 1 fingerprint {}: {}'.format(
            fingerprints, list_keys_output)
    return fingerprints[0].replace(' ', '').upper()


def parse_algorithm_params(gpg_algorithm_text):
    """
    return {
        'algorithm': '...',
        'length_bits': '<bits or None>',
        'ecc_curve': '<curve or None>',
    }
    """

    ecc_algorithms = dict(CryptographicKey.ECC_CURVE_CHOICES).keys()

    if gpg_algorithm_text in ecc_algorithms:
        return {
            'algorithm': 'ECC',
            'ecc_curve': gpg_algorithm_text,
            'length_bits': None
        }

    else:
        try:
            return parse_algo_with_bits(gpg_algorithm_text)
        except ValueError:
            return {
                'algorithm': '',  # blank means unknown
                'ecc_curve': '',  # blank means unknown
                'length_bits': None
            }


def parse_algo_with_bits(gpg_algorithm):
    algo = None

    match = re.match('^(?P<algo>(rsa|dsa|elg))(?P<bits>\d+)', gpg_algorithm)

    if match:
        algo = {
            'rsa': 'RSA',
            'dsa': 'DSA',
            'elg': 'ELGAMAL',
        }.get(match.group('algo'), None)

    if algo is None:
        raise ValueError('Unrecognised algorithm line `{}`'.format(
            gpg_algorithm))

    return {
        'algorithm': algo,
        'length_bits': int(match.group('bits')),
        'ecc_curve': None,
    }


def _parse_pub_line(list_keys_output):
    """
    `pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC] [expires: 2017-12-22]`
    `pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC]
    """

    pub_lines = list(filter(
        lambda l: l.startswith('pub'), list_keys_output.split('\n')
    ))

    assert len(pub_lines) == 1

    return parse_pub_or_sub_line(pub_lines[0])


def _parse_subkey_lines(list_keys_output):
    """
    `sub   elg2048/0x8D79AF8CBF15B67A 2009-09-14 [E] [expired: 2017-03-12]`
    `sub   rsa2048/0x827349966466A87E 2017-12-13 [S] [expires: 2018-12-08]`
    """
    sub_lines = list(filter(
        lambda l: l.startswith('sub'), list_keys_output.split('\n')
    ))

    return [parse_pub_or_sub_line(line) for line in sub_lines]


def parse_pub_or_sub_line(line):

    match = re.match(PUB_SUB_PATTERN, line)

    if not match:
        raise RuntimeError("Can't parse line: `{}` with pattern `{}`".format(
            line, PUB_SUB_PATTERN))

    status = match.groupdict().get('status', None)
    status_extra = match.groupdict().get('status_data', None)

    if status in ('expired', 'expires') and status_extra == 'never':
        expiry_date = None
        revoked = False

    elif status in ('expired', 'expires'):
        expiry_date = parse_date(status_extra)
        revoked = False

    elif status == 'revoked':
        expiry_date = None
        revoked = True

    else:
        expiry_date = None
        revoked = False

    created_date = parse_date(match.group('created_date'))

    result = {
        'long_id': match.group('long_id'),
        'created_date': created_date,
        'expiry_date': expiry_date,
        'revoked': revoked,
        'capabilities': list(match.group('capabilities')),
    }
    result.update(parse_algorithm_params(match.group('algorithm')))
    return result


def parse_date(date_string):
    match = re.match(
        '(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d)',
        date_string
    )

    if match is not None:
        return datetime.date(
            int(match.group('year')),
            int(match.group('month')),
            int(match.group('day')),
        )
    else:
        raise ValueError('Bad date: `{}`'.format(date_string))


def _parse_uid_lines(list_keys_output):
    """
    `uid                   [ revoked] Someone (comment) <a@example.com>`
    `uid                   [ expired] Someone <b@example.com}`
    `uid                   [ unknown] Someone [thisisvalid] <a@example.com>`

    """

    for line in list_keys_output.split('\n'):
        match = re.match('^uid\s+\[(?P<status>.*?)\] (?P<uid>.*)$', line)
        if match is not None:
            status = match.group('status').strip()
            if status not in ('unknown', 'revoked', 'expired', 'ultimate'):
                raise RuntimeError(status)

            if status not in ('revoked', 'expired'):
                yield match.group('uid')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    LOG = logging.getLogger('')
    print(parse_public_key(sys.argv[1]))
