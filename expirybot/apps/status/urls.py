from django.conf.urls import url

from .views import StatusView

urlpatterns = [

    url(
        r'^_status/$',
        StatusView.as_view(),
        name='status.status'
    ),

]
