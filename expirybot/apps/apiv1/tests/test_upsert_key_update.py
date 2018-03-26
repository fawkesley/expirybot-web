from django.utils import timezone
from django.contrib.auth.models import User, Permission

from rest_framework.test import APISimpleTestCase

from nose.tools import assert_equal

from expirybot.apps.keys.models import KeyUpdate


class TestGetUnsubscribeLinkView(APISimpleTestCase):
    HASH_1 = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    HASH_2 = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    FINGERPRINT_1 = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    FINGERPRINT_2 = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'

    @classmethod
    def setUpClass(cls):
        cls.now = timezone.now()

        cls.api_user = User.objects.create(username='apiuser')
        cls.api_user.user_permissions.add(
            Permission.objects.get(codename='add_key_update')
        )

        KeyUpdate.objects.all().delete()

    @classmethod
    def tearDownClass(cls):
        cls.api_user.delete()
        KeyUpdate.objects.all().delete()

    def test_requires_auth(self):
        response = self.client.post(
            '/apiv1/key-update-messages/',
            {
                'sks_hash': self.HASH_1,
                'fingerprint': self.FINGERPRINT_1,
                'updated_at': self.now,
            },
        )
        assert_equal(401, response.status_code)

    def test_create(self):
        self.client.force_authenticate(self.api_user)

        response = self.client.post(
            '/apiv1/key-update-messages/',
            {
                'sks_hash': self.HASH_1,
                'fingerprint': self.FINGERPRINT_1,
                'updated_at': self.now,
            },
        )
        assert_equal(201, response.status_code)

        update = KeyUpdate.objects.get()

        assert_equal(self.HASH_1, update.sks_hash)
        assert_equal(self.FINGERPRINT_1, update.fingerprint)
        assert_equal(self.now, update.updated_at)

        update.delete()

    def test_update(self):
        self.client.force_authenticate(self.api_user)

        response = self.client.post(
            '/apiv1/key-update-messages/',
            {
                'sks_hash': self.HASH_1,
                'fingerprint': self.FINGERPRINT_1,
                'updated_at': self.now,
            },
        )
        assert_equal(201, response.status_code)

        response = self.client.post(
            '/apiv1/key-update-messages/',
            {
                'sks_hash': self.HASH_1,
                'fingerprint': self.FINGERPRINT_2,
                'updated_at': self.now,
            },
        )
        assert_equal(200, response.status_code)

        update = KeyUpdate.objects.get()

        assert_equal(self.HASH_1, update.sks_hash)
        assert_equal(self.FINGERPRINT_2, update.fingerprint)
        assert_equal(self.now, update.updated_at)
