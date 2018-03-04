from django.conf.urls import url

from .views import PGPKeyDetailView, KeyTestResultView, TestPGPKeyView

V4_FINGERPRINT_PATTERN = "[A-Z0-9]{40}"
V3_FINGERPRINT_PATTERN = "[A-Z0-9]{16}"

UUID_PATTERN = (
    '[0-9a-fA-F]{8}-'
    '[0-9a-fA-F]{4}-'
    '[0-9a-fA-F]{4}-'
    '[0-9a-fA-F]{4}-'
    '[0-9a-fA-F]{12}'
)

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

    url(
        r'^test-pgp-key/$',
        TestPGPKeyView.as_view(),
        name='keys.test-pgp-key'
    ),

    url(
        r'^test-pgp-key/(?P<pk>' + UUID_PATTERN + ')/$',
        KeyTestResultView.as_view(),
        name='keys.key-test-result'
    ),


]
