import random
import re
from django.db import transaction


def make_user_permanent(user, email_address):
    assert user.profile.is_temporary, ('Non-temporary user `{}` cannot be '
                                       'made permanent')

    assert not user.email, ('"temporary" user `{}` already has an email '
                            'set: `{}`').format(user, user.email)

    with transaction.atomic():
        user.username = _make_auto_username(email_address)
        user.email = email_address
        user.save()


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
