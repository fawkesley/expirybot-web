import datetime
from nose.tools import assert_equal
from django.test import TestCase
from .gpg_wrapper import parse_pub_or_sub_line


def assert_no_raise(func):
    try:
        func()
    except Exception as e:
        assert False, "function raised: {}".format(repr(e))


class TestPubOrSubLineParser(TestCase):
    def _test_parse_pub(self, line, expected):
        got = parse_pub_or_sub_line(line)

        for key, expected_value in expected.items():
            assert_equal(got[key], expected_value)

    def test_parse_general_structure(self):
        self._test_parse_pub(
            'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC]',  # noqa
            {
                'algorithm': 'RSA',
                'capabilities': ['S', 'C'],
                'created_date': datetime.date(2014, 10, 31),
                'expiry_date': None,
                'length_bits': 4096,
                'long_id': '309F635DAD1B5517',
                'revoked': False
            }
        )

    def test_parse_no_expiry(self):
        self._test_parse_pub(
            'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC]',  # noqa
            {
                'expiry_date': None,
                'revoked': False
            }
        )

    def test_expiry_date(self):
        self._test_parse_pub(
            'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'created_date': datetime.date(2014, 10, 31),
                'expiry_date': datetime.date(2017, 12, 22),
                'revoked': False
            }
        )

    def test_already_expired(self):
        self._test_parse_pub(
            'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC] [expired: 2017-12-22]',  # noqa
            {
                'created_date': datetime.date(2014, 10, 31),
                'expiry_date': datetime.date(2017, 12, 22),
                'revoked': False
            }
        )

    def test_revoked(self):
        self._test_parse_pub(
            'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SCA] [revoked: 2018-01-15]',  # noqa
            {
                'created_date': datetime.date(2014, 10, 31),
                'expiry_date': None,
                'revoked': True
            }
        )

    def test_dsa(self):
        self._test_parse_pub(
            'pub   dsa1024/0xDEADBEEFDEADBEEF 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'algorithm': 'DSA',
                'ecc_curve': None,
                'length_bits': 1024
            }
        )

    def test_elgamal(self):
        self._test_parse_pub(
            'pub   elg1024/0xDEADBEEFDEADBEEF 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'algorithm': 'ELGAMAL',
                'ecc_curve': None,
                'length_bits': 1024
            }
        )

    def test_brainpool_256(self):
        self._test_parse_pub(
            'pub   brainpoolP256r1/0xDEADBEEFDEADBEEF 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'algorithm': 'ECC',
                'ecc_curve': 'brainpoolP256r1',
                'length_bits': None
            }
        )

    def test_ed25519(self):
        self._test_parse_pub(
            'pub   ed25519/0xDEADBEEFDEADBEEF 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'algorithm': 'ECC',
                'ecc_curve': 'ed25519',
                'length_bits': None
            }
        )

    def test_curve25519(self):
        self._test_parse_pub(
            'pub   curve25519/0xDEADBEEFDEADBEEF 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'algorithm': 'ECC',
                'ecc_curve': 'curve25519',
                'length_bits': None
            }
        )

    def test_unknown_algorithm(self):
        self._test_parse_pub(
            'pub   unknown123/0xDEADBEEFDEADBEEF 2014-10-31 [SC] [expires: 2017-12-22]',  # noqa
            {
                'algorithm': None,
                'ecc_curve': None,
                'length_bits': None
            }
        )
