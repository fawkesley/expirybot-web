from django.conf.urls import url

from .views import (
    AddEmailAddressView, AddEmailConfirmSendView, EmailSentView, LoginView,
    LoginEmailSentView, LoginGetEmailAddressView, LoginFromEmailLinkView,
    LoginWithContextView, LogoutView, MonitorEmailAddressView, SignUpView,
    SignUpWithContextView, UserSettingsView
)

JWT_PATTERN = "[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*"


urlpatterns = [

    url(
        r'^monitor-email-address/$',
        MonitorEmailAddressView.as_view(),
        name='users.monitor-email-address'
    ),

    url(
        r'^u/login-with-password/$',
        LoginView.as_view(),
        name='users.login-with-password'
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
        r'^u/login/email-sent/$',
        LoginEmailSentView.as_view(),
        name='users.login-email-sent'
    ),

    url(r'^u/logout/', LogoutView.as_view(), name='users.logout'),

    url(
        r'^u/sign-up/$',
        SignUpView.as_view(),
        name='users.sign-up'
    ),
    url(
        r'^u/sign-up/(?P<login_context>[a-z\-]+)/$',
        SignUpWithContextView.as_view(),
        name='users.sign-up-with-context'
    ),

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
]
