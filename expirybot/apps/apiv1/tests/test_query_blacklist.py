from django.utils import timezone

from rest_framework.test import APISimpleTestCase

from nose.tools import assert_equal

from expirybot.apps.blacklist.models import EmailAddress, BlacklistedDomain


class TestGetUnsubscribeLinkView(APISimpleTestCase):

    @classmethod
    def setUpClass(cls):
        now = timezone.now()

        cls.ok = EmailAddress.objects.create(
            email_address='ok@example.com',
            unsubscribe_datetime=None,
            complain_datetime=None,
            last_bounce_datetime=None
        )

        cls.unsubscriber = EmailAddress.objects.create(
            email_address='unsubscriber@example.com',
            unsubscribe_datetime=now,
            complain_datetime=None,
            last_bounce_datetime=None
        )

        cls.complainer = EmailAddress.objects.create(
            email_address='complainer@example.com',
            unsubscribe_datetime=now,
            complain_datetime=None,
            last_bounce_datetime=None
        )

        cls.bouncer = EmailAddress.objects.create(
            email_address='bouncer@example.com',
            unsubscribe_datetime=None,
            complain_datetime=now,
            last_bounce_datetime=None
        )

        BlacklistedDomain.objects.create(domain='blacklisted.com')

    @classmethod
    def tearDownClass(cls):
        EmailAddress.objects.all().delete()
        BlacklistedDomain.objects.all().delete()

    def test_ok_for_not_blacklisted_email(self):
        self._assert_not_blacklisted('ok@example.com')

    def test_not_ok_for_unsubscriber(self):
        self._assert_is_blacklisted('unsubscriber@example.com')

    def test_not_ok_for_complainer(self):
        self._assert_is_blacklisted('complainer@example.com')

    def test_not_ok_for_bouncer(self):
        self._assert_is_blacklisted('bouncer@example.com')

    def test_not_ok_for_blacklisted_domain(self):
        self._assert_is_blacklisted('someone@blacklisted.com')

    def _assert_is_blacklisted(self, email):
        response = self.client.get(
            '/apiv1/blacklist/unsubscribe-link/',
            {'email_address': email},
        )
        assert_equal(200, response.status_code)
        assert_equal({'allow_email': False}, response.data)

    def _assert_not_blacklisted(self, email):
        response = self.client.get(
            '/apiv1/blacklist/unsubscribe-link/',
            {'email_address': email},
        )
        assert_equal(200, response.status_code)
        assert_equal({'allow_email': True}, response.data)
