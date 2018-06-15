from rest_framework.views import APIView
from rest_framework.exceptions import APIException


import logging
LOG = logging.getLogger(__file__)


class NotAcceptableError(APIException):
    status_code = 406


class MailgunWebhookBounce(APIView):
    def post(self, request, *args, **kwargs):
        raise NotAcceptableError('Endpoint not yet implemented.')
