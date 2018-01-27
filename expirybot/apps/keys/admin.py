from django.contrib import admin

from .models import PGPKey, UID


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

    readonly_fields = (
        'uid_string',
    )

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


@admin.register(PGPKey)
class PGPKeyAdmin(ReadonlyFieldsOnChangeMixin, admin.ModelAdmin):
    list_display = (
        '__str__',
        'key_algorithm',
        'key_length_bits',
        'revoked',
        'expiry_datetime',
        'uids_string',
        'last_synced',
        'keyserver',
    )

    list_filter = (
        'creation_datetime',
        'revoked',
        'expiry_datetime',
        'last_synced',
        'key_algorithm',
        'key_length_bits',
    )

    search_fields = (
        'fingerprint',
        'uids_set__uid_string',
    )

    inlines = (UIDInline,)
    readonly_fields_on_change = ('fingerprint',)

    def keyserver(self, instance):
        return (
            '<a href="https://keyserver.paulfurley.com'
            '/pks/lookup?op=vindex&search={}">[keyserver]</a>').format(
                    instance.zero_x_fingerprint
        )

    keyserver.allow_tags = True
