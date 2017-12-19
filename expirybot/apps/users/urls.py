from django.conf.urls import url

from .views import MonitorEmailAddressView, UserSettingsView


urlpatterns = [
    url(
        r'^monitor-email-address/$',
        MonitorEmailAddressView.as_view(),
        name='users.monitor-email-address'
    ),

    url(
        r'^u/settings/$',
        UserSettingsView.as_view(),
        name='users.settings'
    ),
]
