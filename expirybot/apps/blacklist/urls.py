from django.conf.urls import url

from .views import UnsubscribeEmailView
#
# UUID_PATTERN = (
#     '[0-9a-fA-F]{8}-'
#     '[0-9a-fA-F]{4}-'
#     '[0-9a-fA-F]{4}-'
#     '[0-9a-fA-F]{4}-'
#     '[0-9a-fA-F]{12}'
# )
#

JWT_PATTERN = "[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"

urlpatterns = [
    url(
        r'^unsubscribe/(?P<json_web_token>' + JWT_PATTERN + ')/$',
        UnsubscribeEmailView.as_view(),
        name='unsubscribe-email'
    ),

]
