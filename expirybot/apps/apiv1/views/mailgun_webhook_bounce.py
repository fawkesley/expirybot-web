from rest_framework.views import APIView
from rest_framework.exceptions import APIException


import logging
LOG = logging.getLogger(__file__)


class UnprocessableError(APIException):
    status_code = 416


class MailgunWebhookBounce(APIView):
    def post(self, request, *args, **kwargs):
        raise UnprocessableError('Endpoint not yet implemented.')
