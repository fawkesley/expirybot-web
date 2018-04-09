import datetime
import logging
import random
import re

import jwt

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from expirybot.apps.blacklist.models import EmailAddress
from expirybot.apps.users.models import UserProfile

LOG = logging.getLogger(__name__)


def get_user_for_email_address(email):
    """
    Return the django.contrib.auth.User or None for a given email address.
    """

    try:
        email_model = EmailAddress.objects.get(email_address=email)

    except EmailAddress.DoesNotExist:
        return None

    owner_profile = email_model.owner_profile

    if owner_profile is not None:
        return owner_profile.user
    else:
        return None


def make_user_permanent(user, email_address):
    assert user.profile.is_temporary, ('Non-temporary user `{}` cannot be '
                                       'made permanent')

    assert not user.email, ('"temporary" user `{}` already has an email '
                            'set: `{}`').format(user, user.email)

    with transaction.atomic():
        user.username = _make_auto_username(email_address)
        user.email = email_address
        user.save()

        LOG.info('New user {}'.format(user.username))


def _make_auto_username(email_address):
    """
    valid chars: @.+-_ and letters & digits
    """

    def _sanitised_email(email_address):
        max_length = 150 - len('auto--12345678')
        return re.sub('[^.@a-z0-9]', '', email_address.lower())[0:max_length]

    def _eight_random_characters():
        chars = 'abcdefghjkmnpqrstuvwxyz'
        return ''.join(random.choice(chars) for x in range(8))

    return 'auto-{email}-{rnd}'.format(
        email=_sanitised_email(email_address),
        rnd=_eight_random_characters()
    )


def make_authenticated_one_click_config_url(user_profile, key, value):
    """
    Make a URL which, when clicked, will set the given UserProfile.key to the
    given value.
    """
    def make_json_web_token(user_profile):
        data = {
            'exp': timezone.now() + datetime.timedelta(days=90),
            'a': 'one-click-config',
            'u': str(user_profile.uuid),
            'k': key,
            'v': value,
        }

        result = jwt.encode(data, settings.SECRET_KEY)
        return result

    assert key in UserProfile.ALLOWED_ONE_CLICK_SETTINGS

    return '{base_url}{path}'.format(
        base_url=settings.EXPIRYBOT_BASE_URL,
        path=reverse(
            'users.one-click-config',
            kwargs={
                'json_web_token': make_json_web_token(user_profile)
            }
        )
    )
