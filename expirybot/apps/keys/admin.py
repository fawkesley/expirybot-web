from django.contrib import admin
from django.shortcuts import reverse

from .models import BrokenKey, PGPKey, Subkey, UID


class ReadonlyFieldsOnChangeMixin():
    def get_readonly_fields(self, request, obj):
        readonly_fields = list(super(
            ReadonlyFieldsOnChangeMixin, self
        ).get_readonly_fields(request, obj))

        if obj:  # make uuid readonly if the model is already in DB
            readonly_fields.extend(self.readonly_fields_on_change)

        return tuple(readonly_fields)


class UIDInline(admin.TabularInline):
    model = UID

    fields = (
        'uid_string',
    )

    readonly_fields = fields

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class SubkeyInline(admin.TabularInline):
    model = Subkey

    fields = (
        'long_id',
        'friendly_type',
        'creation_date',
        'expiry_date',
        'revoked',
        'capabilities',
    )

    readonly_fields = fields

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(PGPKey)
class PGPKeyAdmin(ReadonlyFieldsOnChangeMixin, admin.ModelAdmin):
    list_display = (
        '__str__',
        'friendly_type',
        'capabilities',
        'revoked',
        'uids_string',
        'num_subkeys',
        'keyserver',
        'details',
    )

    list_filter = (
        'creation_date',
        'revoked',
        'expiry_date',
        'last_synced',
        'key_algorithm',
        'key_length_bits',
    )

    search_fields = (
        'fingerprint',
        'uids_set__uid_string',
    )

    inlines = (UIDInline, SubkeyInline)

    readonly_fields = (
        'key_algorithm',
        'key_length_bits',
        'capabilities',
        'revoked',
        'creation_date',
        'expiry_date',
    )
    readonly_fields_on_change = ('fingerprint',)

    def keyserver(self, instance):
        return (
            '<a href="https://keyserver.paulfurley.com'
            '/pks/lookup?op=vindex&search={}">[keyserver]</a>').format(
                    instance.zero_x_fingerprint
        )

    keyserver.allow_tags = True

    def details(self, instance):
        return '<a href="{}">[deets]</a>'.format(
            reverse(
                'keys.key-detail',
                kwargs={'pk': instance.fingerprint}
            )
        )

    details.allow_tags = True

    def num_subkeys(self, model):
        return model.subkeys.count()


@admin.register(BrokenKey)
class BrokenKeyAdmin(ReadonlyFieldsOnChangeMixin, admin.ModelAdmin):
    list_display = (
        '__str__',
        'next_retry_sync',
    )

    readonly_fields_on_change = ('fingerprint',)
