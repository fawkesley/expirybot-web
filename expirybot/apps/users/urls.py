from django.conf.urls import url

from .views import MonitorEmailAddressView


urlpatterns = [
    url(
        r'^monitor-email-address/$',
        MonitorEmailAddressView.as_view(),
        name='users.monitor-email-address'
    ),
]
