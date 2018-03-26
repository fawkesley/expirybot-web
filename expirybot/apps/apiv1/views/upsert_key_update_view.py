from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework import permissions
from rest_framework import serializers
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.generics import CreateAPIView, UpdateAPIView


from expirybot.apps.keys.models import KeyUpdate

import logging
LOG = logging.getLogger(__file__)


class KeyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyUpdate
        fields = ('sks_hash', 'fingerprint', 'updated_at')


class InvalidQueryError(APIException):
    status_code = 400


class UpsertKeyUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_anonymous():
            return False

        # See the corresponding KeyUpdateModel `permissions` Meta property
        return request.user.has_perm('keys.add_key_update')


class UpsertKeyUpdateView(CreateAPIView, UpdateAPIView):
    permission_classes = (UpsertKeyUpdatePermission,)
    queryset = KeyUpdate.objects.all
    serializer_class = KeyUpdateSerializer

    def create(self, request, *args, **kwargs):
        if self.get_object():

            return super(UpsertKeyUpdateView, self).update(
                request, *args, **kwargs
            )
        else:
            return super(UpsertKeyUpdateView, self).create(
                request, *args, **kwargs
            )

    def get_object(self):
        try:
            return KeyUpdate.objects.get(sks_hash=self.request.data['sks_hash'])
        except KeyUpdate.DoesNotExist:
            return None
