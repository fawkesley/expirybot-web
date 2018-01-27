import datetime
import subprocess
import sys
import logging
import re

from os.path import abspath, dirname, join as pjoin

from django.conf import settings


LOG = logging.getLogger(__name__)
GPG2_SANDBOXED = abspath(pjoin(dirname(__file__), 'gpg2_sandboxed'))


class GPGError(RuntimeError):
    pass


def parse_public_key(pgp_key_filename):
    fingerprint = get_fingerprint(pgp_key_filename)

    import_key(pgp_key_filename)

    parsed = parse_list_keys(fingerprint)

    return parsed


def encrypt_message(fingerprint, text):
    _receive_key(fingerprint)
    return _encrypt_text(fingerprint, text)


def get_fingerprint(pgp_key_filename):
    stdout = stdout_for_subprocess([
        GPG2_SANDBOXED, pgp_key_filename
    ])
    return _parse_fingerprint_line(stdout)


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


def import_key(pgp_key_filename):
    LOG.info("importing key")
    stdout_for_subprocess([
        GPG2_SANDBOXED, '--import', pgp_key_filename
    ])


def parse_list_keys(fingerprint):
    stdout = stdout_for_subprocess([
        GPG2_SANDBOXED, '--list-keys', fingerprint
    ])

    return {
        'fingerprint': _parse_fingerprint_line(stdout),
        'algorithm': _parse_algorithm(stdout),
        'length_bits': _parse_length_bits(stdout),
        'created_date': _parse_created_date(stdout),
        'expiry_date': _parse_expiry_date(stdout),
        'uids': list(_parse_uid_lines(stdout)),
        'subkeys': list(_parse_subkey_lines(stdout)),
    }


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
        LOG.info(line)
        match = re.match('^\s*Key fingerprint = (?P<fingerprint>.*)$', line)

        if match is not None:
            fingerprints.append(match.group('fingerprint'))

    assert len(fingerprints) == 1, '{}: {}'.format(
            fingerprints, list_keys_output)
    return fingerprints[0].replace(' ', '').upper()


def _parse_expiry_date(list_keys_output):
    return _parse_pub_line(list_keys_output)['expiry_date']


def _parse_created_date(list_keys_output):
    return _parse_pub_line(list_keys_output)['created_date']


def _parse_algorithm(list_keys_output):
    conversion = {
        'rsa': 'RSA',
        'dsa': 'DSA',
        'elg': 'ELGAMAL',
    }
    return conversion.get(
        _parse_pub_line(list_keys_output)['algorithm'],
        None
    )


def _parse_length_bits(list_keys_output):
    return _parse_pub_line(list_keys_output)['length_bits']


def _parse_pub_line(list_keys_output):
    """
    `pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC] [expires: 2017-12-22]`
    `pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC]
    """

    pub_lines = list(filter(
        lambda l: l.startswith('pub'), list_keys_output.split('\n')
    ))

    assert len(pub_lines) == 1

    pattern = r'^pub\s+ (?P<algorithm>[^0-9]+)(?P<length_bits>[0-9]+)\/0x[0-9A-F]{16} (?P<created_date>\d{4}-\d{2}-\d{2}) \[(?P<capabilities>[AECS]+)\]( \[(?P<status>expires|expired|revoked): (?P<status_date>\d{4}-\d{2}-\d{2})\])?$'  # noqa

    match = re.match(pattern, pub_lines[0])

    if not match:
        raise RuntimeError("Can't parse line: `{}` with pattern `{}`".format(
            pub_lines[0], pattern))

    status = match.groupdict().get('status', None)

    if status in ('expired', 'expires'):
        expiry_date = parse_date(match.group('status_date'))
        revoked = False

    elif status == 'revoked':
        expiry_date = None
        revoked = True

    else:
        expiry_date = None
        revoked = False

    created_date = parse_date(match.group('created_date'))

    return {
        'created_date': created_date,
        'expiry_date': expiry_date,
        'revoked': revoked,
        'algorithm': match.group('algorithm'),
        'length_bits': int(match.group('length_bits')),
    }


def parse_date(date_string):
    return datetime.date(*map(int, date_string.split('-')))


def _parse_uid_lines(list_keys_output):
    """
    `uid                   [ revoked] Someone (comment) <a@example.com>`
    `uid                   [ expired] Someone <b@example.com}`
    """

    for line in list_keys_output.split('\n'):
        match = re.match('^uid\s+\[(?P<status>.*)\] (?P<uid>.*)$', line)
        if match is not None:
            status = match.group('status').strip()
            if status not in ('unknown', 'revoked', 'expired'):
                raise RuntimeError(status)

            if status not in ('revoked', 'expired'):
                yield match.group('uid')


def _parse_subkey_lines(list_packets_output):
    """
    `sub   elg2048/0x8D79AF8CBF15B67A 2009-09-14 [E] [expired: 2017-03-12]`
    `sub   rsa2048/0x827349966466A87E 2017-12-13 [S] [expires: 2018-12-08]`
    """
    return []


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    LOG = logging.getLogger('')
    print(parse_public_key(sys.argv[1]))
