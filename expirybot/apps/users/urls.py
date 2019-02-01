from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from .views import (
    AddEmailAddressView, AddEmailConfirmSendView,
    AdminAllEmailAddressesView,
    AdminFeedbackEmailAddressesView, AdminListUsers, EmailSentView,
    LoginEmailSentView, LoginGetEmailAddressView, LoginFromEmailLinkView,
    LoginWithContextView, LogoutView, MonitorEmailAddressView,
    OneClickConfigView, ProveKeyOwnershipView,
    ProveKeyOwnershipFromEmailLinkView, UserSettingsView
)

JWT_PATTERN = "[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"
V4_FINGERPRINT_PATTERN = "[A-Z0-9]{40}"
V3_FINGERPRINT_PATTERN = "[A-Z0-9]{16}"

urlpatterns = [

    url(
        r'^admin/list-users/$',
        staff_member_required(AdminListUsers.as_view()),
        name='admin-list-users'
    ),

    url(
        r'^admin/all-email-addresses/$',
        staff_member_required(AdminAllEmailAddressesView.as_view()),
        name='admin-all-email-addresses'
    ),

    url(
        r'^admin/feedback-email-addresses/$',
        staff_member_required(AdminFeedbackEmailAddressesView.as_view()),
        name='admin-feedback-email-addresses'
    ),

    url(
        r'^monitor-email-address/$',
        MonitorEmailAddressView.as_view(),
        name='users.monitor-email-address'
    ),

    url(
        r'^u/login/reason/(?P<login_context>[a-z\-]+)/$',
        LoginWithContextView.as_view(),
        name='users.login-with-context'
    ),

    url(
        r'^u/login/$',
        LoginGetEmailAddressView.as_view(),
        name='users.login'
    ),

    url(
        r'^u/login/(?P<json_web_token>' + JWT_PATTERN + ')/$',
        LoginFromEmailLinkView.as_view(),
        name='users.login-from-email-link'
    ),

    url(
        r'^cfg/(?P<json_web_token>' + JWT_PATTERN + ')/$',
        OneClickConfigView.as_view(),
        name='users.one-click-config'
    ),

    url(
        r'^u/login/email-sent/$',
        LoginEmailSentView.as_view(),
        name='users.login-email-sent'
    ),

    url(r'^u/logout/', LogoutView.as_view(), name='users.logout'),

    url(
        r'^u/add-email-address/confirm-send/'
        '(?P<b64_email_address>[A-Za-z0-9+/=]+)/$',
        AddEmailConfirmSendView.as_view(),
        name='users.add-email-confirm-send'
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

    url(
        r'^u/settings/prove/(?P<pk>' + V4_FINGERPRINT_PATTERN + ')/$',
        ProveKeyOwnershipView.as_view(),
        name='users.prove-key-ownership'
    ),

    url(
        r'^u/settings/prove/(?P<pk>' + V3_FINGERPRINT_PATTERN + ')/$',
        ProveKeyOwnershipView.as_view(),
        name='users.prove-key-ownership'
    ),

    url(
        r'^u/settings/prove/(?P<json_web_token>' + JWT_PATTERN + ')/$',
        ProveKeyOwnershipFromEmailLinkView.as_view(),
        name='users.prove-key-ownership-from-email-link'
    ),

]
