import logging

from django.views.generic import TemplateView

from .mixins import EmailAddressContextFromURLMixin

LOG = logging.getLogger(__name__)


class EmailSentView(EmailAddressContextFromURLMixin, TemplateView):
    template_name = 'users/email_sent.html'
