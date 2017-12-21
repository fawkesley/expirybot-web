from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile, EmailAddressOwnershipProof


@admin.register(EmailAddressOwnershipProof)
class EmailAddressOwnershipProofAdmin(admin.ModelAdmin):
    list_display = (
        'profile',
        'email_address',
    )

    list_filter = (
        'profile',
    )


#class EmailAddressOwnershipProofInline(admin.ModelAdmin):
#    readonly_fields = ('profile', 'email_address')

class EmailAddressOwnershipProofInline(admin.StackedInline):
    model = EmailAddressOwnershipProof
    # readonly_fields = ('profile', 'email_address')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__',)
    inlines = (EmailAddressOwnershipProofInline,)


class UserProfileInline(admin.StackedInline):
    # Define an inline admin descriptor for UserProfile model
    # which acts a bit like a singleton
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

    readonly_fields = ('created_at', 'updated_at')

    inlines = (EmailAddressOwnershipProofInline,)


class UserAdmin(BaseUserAdmin):
    # Define a new User admin
    inlines = (UserProfileInline, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
