from django.conf.urls import url

from .views import GetUnsubscribeLinkView

urlpatterns = [

    url(
        r'blacklist/unsubscribe-link/$',
        GetUnsubscribeLinkView.as_view(),
        name='apiv1.blacklist.unsubscribe-link'
    ),

]
