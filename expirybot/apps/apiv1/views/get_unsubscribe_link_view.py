from django.shortcuts import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import permissions

from expirybot.apps.blacklist.models import EmailAddress
from expirybot.libs.uid_parser import roughly_validate_email

from expirybot.apps.blacklist.utils import (
    allow_send_email, make_authenticated_unsubscribe_url
)
from expirybot.apps.status.models import EventLatestOccurrence

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
    """
    This is used *only* by Expirybot 'classic' (3-day expiry emails) to get
    an unsubscribe link for the given email address.

    The view either returns 'allow_email': True with an unsubscribe link
    OR or returns 'allow_email': False with no link.

    This way the bot can make a single API call to ask permission AND the
    unsubscribe link.

    Scenarios:

    - they're globally unsubscribed / bounced / complained: (DENY)
    - we know nothing about this email (allow, UNSUBSCRIBE link)
    - they're subscribed & opted in to expiry reminders (allow + SETTINGS link)
    - they're subscribed & opted out of expiry reminders (DENY)
    """
    permission_classes = (GetUnsubscribeLinkPermission,)

    def get(self, request, *args, **kwargs):
        try:
            email_address = request.query_params['email_address']
        except KeyError:
            LOG.warn('Got query with no email_address')
            raise InvalidQueryError('Missing email, try ?email_address=<...>')

        else:
            if not roughly_validate_email(email_address):
                LOG.warn('unsubscribe link for bad email `{}`'.format(
                    email_address))
                raise InvalidQueryError('Invalid email address `{}`'.format(
                    email_address))

        EventLatestOccurrence.record_event('api-call-unsubscribe-url')

        if not allow_send_email(email_address):
            return Response({'allow_email': False})

        profile = self._get_profile(email_address)

        if not profile:
            unsubscribe_all_link = request.build_absolute_uri(
                make_authenticated_unsubscribe_url(email_address)
            )

            return Response({
                'allow_email': True,
                'unsubscribe_link': unsubscribe_all_link
            })

        if profile.notify_expiry:
            settings_link = request.build_absolute_uri(
                reverse('users.login') + '?next={}&email={}'.format(
                    reverse('users.settings'), email_address)
            )

            return Response({
                'allow_email': True,
                'unsubscribe_link': settings_link,
                'unsubscribe_text': (
                    "You're receiving this because you opted in to PGP expiry "
                    "alerts at www.expirybot.com. Adjust your notification "
                    "settings:"
                )
            })
        else:
            return Response({
                'allow_email': False,
            })

    def _get_profile(self, email_address):
        try:
            ob = EmailAddress.objects.get(email_address=email_address)
        except EmailAddress.DoesNotExist:
            return None
        else:
            return ob.owner_profile
