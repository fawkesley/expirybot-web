from django.contrib import admin

from .models import ExampleModel


class ReadonlyFieldsOnChangeMixin():
    def get_readonly_fields(self, request, obj):
        readonly_fields = list(super(
            ReadonlyFieldsOnChangeMixin, self
        ).get_readonly_fields(request, obj))

        if obj:  # make uuid readonly if the model is already in DB
            readonly_fields.extend(self.readonly_fields_on_change)

        return tuple(readonly_fields)


@admin.register(ExampleModel)
class ExampleModelAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'updated_at',
    )

    list_filter = []

    readonly_fields = []

    readonly_fields_on_change = ['uuid']
