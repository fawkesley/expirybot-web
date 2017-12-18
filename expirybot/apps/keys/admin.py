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


@admin.register(PGPKey)
class PGPKeyAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'key_algorithm',
        'key_length_bits',
        'uids_string',
        'last_synced',
        'keyserver',
    )

    list_filter = (
        'key_algorithm',
        'key_length_bits',
        'last_synced',
    )

    inlines = (UIDInline,)
    readonly_fields_on_change = ('fingerprint',)

    def keyserver(self, instance):
        return (
            '<a href="https://keyserver.paulfurley.com'
            '/pks/lookup?op=vindex&search={}">[keyserver]</a>').format(
                    instance.key_id
        )

    keyserver.allow_tags = True
