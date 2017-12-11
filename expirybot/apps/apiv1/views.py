from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import permissions

from expirybot.apps.blacklist.utils import (
    allow_send_email, make_authenticated_unsubscribe_url
)

import logging
LOG = logging.getLogger(__file__)


class InvalidQueryError(APIException):
    status_code = 400


class GetUnsubscribeLinkPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_anonymous():
            return False

        return request.user.has_perm('blacklist.make_unsubscribe_links')


class GetUnsubscribeLinkView(APIView):
    permission_classes = (GetUnsubscribeLinkPermission,)

    def get(self, request, *args, **kwargs):
        try:
            email_address = request.query_params['email_address']
        except KeyError:
            LOG.warn('Got query with no email_address')
            raise InvalidQueryError

        if allow_send_email(email_address):

            link = request.build_absolute_uri(
                make_authenticated_unsubscribe_url(email_address)
            )

            return Response(
                {
                    'allow_email': True,
                    'unsubscribe_link': link
                }
            )
        else:
            return Response({'allow_email': False})
