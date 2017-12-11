from django.contrib import admin

from .models import BlacklistedEmailAddress, BlacklistedDomain


@admin.register(BlacklistedEmailAddress)
class BlacklistedEmailAddressAdmin(admin.ModelAdmin):

    list_display = (
        '__str__',
        'unsubscribed',
        'bounced',
        'unsubscribe_url',
    )

    list_filter = (
        'unsubscribed',
        'bounced',
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
