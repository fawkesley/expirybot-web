from django.conf.urls import url

from .views import UnsubscribeEmailView

JWT_PATTERN = "[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"

urlpatterns = [
    url(
        r'^unsubscribe/(?P<json_web_token>' + JWT_PATTERN + ')/$',
        UnsubscribeEmailView.as_view(),
        name='unsubscribe-email'
    ),

]
