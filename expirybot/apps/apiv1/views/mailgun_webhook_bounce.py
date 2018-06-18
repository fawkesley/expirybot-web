from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from expirybot.apps.blacklist.utils import (
    record_bounce, delete_bounce_from_mailgun, parse_mailgun_date
)

import logging
LOG = logging.getLogger(__file__)


class NotAcceptableError(APIException):
    status_code = 406


class MissingRecipientError(NotAcceptableError):
    pass


class MissingMailgunAuthenticationParametersError(NotAcceptableError):
    pass


class MissingOrInvalidTimestampError(NotAcceptableError):
    pass


class InvalidMailgunSignatureError():
    pass


def validate_mailgun_post(api_key, token, timestamp, signature):
    import hashlib
    import hmac

    return signature == hmac.new(
        key=api_key.encode('utf-8'),
        msg='{}{}'.format(timestamp, token).encode('utf-8'),
        digestmod=hashlib.sha256).hexdigest()


class MailgunWebhookBounce(APIView):
    def post(self, request, *args, **kwargs):
        LOG.info('Mailgun POST: {}'.format(request.POST))
        self._validate_mailgun_signature(request.POST)
        email = self._validate_recipient_email(request.POST)
        bounce_datetime = self._parse_timestamp(request.POST)

        if record_bounce(email, bounce_datetime):
            delete_bounce_from_mailgun(email)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _validate_recipient_email(post):
        try:
            return post['recipient']
        except KeyError as e:
            LOG.exception(e)
            raise MissingRecipientError()

    @staticmethod
    def _parse_timestamp(post):

        try:
            return parse_mailgun_date(post['event']['Date'])
        except (KeyError, ValueError) as e:
            LOG.exception(e)
            raise MissingOrInvalidTimestampError()

    @staticmethod
    def _validate_mailgun_signature(post):
        try:
            token, timestamp, signature = (
                post['token'],
                post['timestamp'],
                post['signature']
            )
        except KeyError as e:
            LOG.exception(e)
            raise MissingMailgunAuthenticationParametersError()

        if not validate_mailgun_post(
                settings.MAILGUN_API_KEY,
                token, timestamp, signature):
            LOG.warning('Invalid Mailgun signature received on inbound POST.')
            raise InvalidMailgunSignatureError()
