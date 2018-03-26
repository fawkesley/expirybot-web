from django.utils import timezone
from django.contrib.auth.models import User, Permission

from rest_framework.test import APISimpleTestCase

from nose.tools import assert_equal

from expirybot.apps.blacklist.models import EmailAddress, BlacklistedDomain
from expirybot.apps.users.models import (
    EmailAddressOwnershipProof, UserProfile
)


class TestGetUnsubscribeLinkView(APISimpleTestCase):

    @classmethod
    def setUpClass(cls):
        now = timezone.now()

        cls.api_user = User.objects.create(username='apiuser')
        cls.api_user.user_permissions.add(
            Permission.objects.get(codename='make_unsubscribe_links')
        )

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

        cls.subscriber_opt_in = EmailAddress.objects.create(
            email_address='opt+in@example.com',
        )

        cls.subscriber_opt_out = EmailAddress.objects.create(
            email_address='opt+out@example.com',
        )

        cls.create_user(
            'opt+in',
            notify_expiry=True,
            connect_email=cls.subscriber_opt_in
        )

        cls.create_user(
            'opt+out',
            notify_expiry=False,
            connect_email=cls.subscriber_opt_out
        )

        BlacklistedDomain.objects.create(domain='blacklisted.com')

    @staticmethod
    def create_user(username, notify_expiry, connect_email):
        u = User.objects.create(username=username)
        u.profile.notify_expiry = notify_expiry
        u.profile.save()

        EmailAddressOwnershipProof.objects.create(
            email_address=connect_email,
            profile=u.profile
        )
        return u

    @classmethod
    def tearDownClass(cls):
        cls.api_user.delete()
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

    def test_ok_for_subscriber_opted_out(self):
        self._assert_not_blacklisted(
            'opt+in@example.com',
            'http://testserver'
            '/u/login/?next=/u/settings/&email=opt+in@example.com'
        )

    def test_not_ok_for_subscriber_opted_out(self):
        self._assert_is_blacklisted('opt+out@example.com')

    def _assert_is_blacklisted(self, email):
        self.client.force_authenticate(self.api_user)

        response = self.client.get(
            '/apiv1/blacklist/unsubscribe-link/',
            {'email_address': email},
        )
        assert_equal(200, response.status_code)
        assert_equal({'allow_email': False}, response.data)

    def _assert_not_blacklisted(self, email, expected_url=None):
        self.client.force_authenticate(self.api_user)
        response = self.client.get(
            '/apiv1/blacklist/unsubscribe-link/',
            {'email_address': email},
        )
        assert_equal(200, response.status_code)
        assert_equal(True, response.data['allow_email'])

        if expected_url is None:
            assert_equal(
                'http://testserver/unsubscribe/',
                response.data['unsubscribe_link'][0:30]
            )
        else:
            assert_equal(
                expected_url,
                response.data['unsubscribe_link'][0:len(expected_url)]
            )

    # TODO: test format of unsubscribe URL and JWT
