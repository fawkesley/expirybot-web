import urllib

import jwt
import datetime
import logging
import requests

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from expirybot.apps.blacklist.models import EmailAddress, BlacklistedDomain

LOG = logging.getLogger(__name__)


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


def record_bounce(email, bounce_datetime):
    obj, new = EmailAddress.objects.get_or_create(email_address=email)
    LOG.info("bounce {} - {}".format(email, bounce_datetime))

    if obj.last_bounce_datetime:
        obj.last_bounce_datetime = max(
            bounce_datetime, obj.last_bounce_datetime
        )
    else:
        obj.last_bounce_datetime = bounce_datetime

    obj.save()
    return True


def delete_bounce_from_mailgun(email):
    url = 'https://api.mailgun.net/v3/{domain}/bounces/{email}'.format(
        domain=settings.MAILGUN_DOMAIN, email=urllib.parse.quote(email)
    )

    response = requests.delete(url, auth=('api', settings.MAILGUN_API_KEY))
    response.raise_for_status()

    LOG.info('Mailgun delete response: {}'.format(response.text))


def parse_mailgun_date(string):
    """
    Example: Tue, 15 Aug 2017 14:27:09 UTC
    """

    fmt = '%a, %d %b %Y %H:%M:%S UTC'
    return datetime.datetime.strptime(string, fmt).replace(tzinfo=timezone.utc)


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
