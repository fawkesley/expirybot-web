from django.conf.urls import url

from .views import PGPKeyDetailView

V4_FINGERPRINT_PATTERN = "[A-Z0-9]{40}"
V3_FINGERPRINT_PATTERN = "[A-Z0-9]{16}"


urlpatterns = [

    url(
        r'^key/0x(?P<pk>' + V4_FINGERPRINT_PATTERN + ')/$',
        PGPKeyDetailView.as_view(),
        name='keys.key-detail'
    ),

    url(
        r'^key/0x(?P<pk>' + V3_FINGERPRINT_PATTERN + ')/$',
        PGPKeyDetailView.as_view(),
        name='keys.key-detail'
    ),


]
