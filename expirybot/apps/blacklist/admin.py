from django.contrib import admin

from .models import EmailAddress, BlacklistedDomain


@admin.register(EmailAddress)
class EmailAddressAdmin(admin.ModelAdmin):

    list_display = (
        '__str__',
        'unsubscribe_datetime',
        'complain_datetime',
        'last_bounce_datetime',
        'unsubscribe_url',
    )

    list_filter = (
        'unsubscribe_datetime',
        'complain_datetime',
        'last_bounce_datetime',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    search_fields = (
        'email_address',
    )

    def unsubscribe_url(self, instance):
        return '<a href="{}">[unsubscribe]</a>'.format(
            instance.make_authenticated_unsubscribe_url()
        )

    unsubscribe_url.allow_tags = True


@admin.register(BlacklistedDomain)
class BlacklistedDomainAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
    )
