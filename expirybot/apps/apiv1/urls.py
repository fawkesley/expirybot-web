from django.conf.urls import url

from .views import (
    GetUnsubscribeLinkView, UpsertKeyUpdateView, MailgunWebhookBounce
)

urlpatterns = [

    url(
        r'blacklist/unsubscribe-link/$',
        GetUnsubscribeLinkView.as_view(),
        name='apiv1.blacklist.unsubscribe-link'
    ),

    url(
        r'key-update-messages/$',
        UpsertKeyUpdateView.as_view(),
        name='apiv1.keys.upsert-key-update'
    ),

    url(
        r'mailgun-webhook/bounce/$',
        MailgunWebhookBounce.as_view(),
        name='apiv1.mailgun-webhook.bounce'
    ),

]
