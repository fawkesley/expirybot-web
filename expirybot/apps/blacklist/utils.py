import jwt
import datetime

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from expirybot.apps.blacklist.models import EmailAddress, BlacklistedDomain


def allow_send_email(email_address):
    return _allow_email_address(email_address) \
            and _allow_domain(_get_domain(email_address))


def make_authenticated_unsubscribe_url(email_address):
    return reverse(
        'unsubscribe-email',
        kwargs={
            'json_web_token': make_json_web_token(email_address)
        }
    )


def make_json_web_token(email_address):
    data = {
        'exp': timezone.now() + datetime.timedelta(days=90),
        'eml': str(email_address),
    }

    result = jwt.encode(data, settings.SECRET_KEY)
    return result



def _allow_email_address(email_address):
    try:
        obj = EmailAddress.objects.get(email_address=email_address)
    except EmailAddress.DoesNotExist:
        return True

    return all(
        x is None for x in (
            obj.unsubscribe_datetime,
            obj.complain_datetime,
            obj.last_bounce_datetime
        )
    )


def _get_domain(email):
    return email.split('@')[-1].lower()


def _allow_domain(domain):
    try:
        BlacklistedDomain.objects.get(domain=domain)
    except BlacklistedDomain.DoesNotExist:
        return True
    else:
        return False
