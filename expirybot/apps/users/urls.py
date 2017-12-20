from django.conf.urls import url

from .views import (
    AddEmailAddressView, EmailSentView, MonitorEmailAddressView,
    UserSettingsView
)

JWT_PATTERN = "[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"


urlpatterns = [
    url(
        r'^monitor-email-address/$',
        MonitorEmailAddressView.as_view(),
        name='users.monitor-email-address'
    ),

    url(
        r'^u/add-email-address/(?P<json_web_token>' + JWT_PATTERN + ')/$',
        AddEmailAddressView.as_view(),
        name='users.add-email-address'
    ),

    url(
        r'^u/add-email-address/email-sent/'
        '(?P<b64_email_address>[A-Za-z0-9+/=]+)/$',
        EmailSentView.as_view(),
        name='users.email-sent'
    ),

    url(
        r'^u/settings/$',
        UserSettingsView.as_view(),
        name='users.settings'
    ),
]
