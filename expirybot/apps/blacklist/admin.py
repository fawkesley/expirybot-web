from django.contrib import admin

from .models import BlacklistedEmailAddress, BlacklistedDomain


@admin.register(BlacklistedEmailAddress)
class BlacklistedEmailAddressAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'unsubscribed',
        'bounced',
    )

    list_filter = (
        'unsubscribed',
        'bounced',
    )


@admin.register(BlacklistedDomain)
class BlacklistedDomainAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
    )
