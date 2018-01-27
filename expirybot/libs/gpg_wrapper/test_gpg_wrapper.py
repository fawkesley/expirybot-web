from django.test import TestCase
from .gpg_wrapper import _parse_pub_line


PUB_LINES = [
    'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC]',
    'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC] [expires: 2017-12-22]',
    'pub   rsa4096/0x309F635DAD1B5517 2014-10-31 [SC] [expired: 2017-12-22]',
    'pub   rsa4096/0x309F635DAD1B5517 2015-01-16 [SCA] [revoked: 2018-01-15]',
]


def assert_no_raise(func):
    try:
        func()
    except Exception as e:
        assert False, "function raised: {}".format(repr(e))


class TestParsePubLine(TestCase):
    def test_parse_pub_line(self):
        for line in PUB_LINES:
            assert_no_raise(lambda: _parse_pub_line(line))
