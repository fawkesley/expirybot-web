import base64
import logging
import uuid


from django.db import transaction

from django.contrib.auth import login
from django.contrib.auth.models import User

from django.shortcuts import redirect, reverse
from django.views.generic.edit import FormView

from ..forms import MonitorEmailAddressForm

LOG = logging.getLogger(__name__)


class MonitorEmailAddressView(FormView):
    template_name = 'users/monitor_email_address.html'
    form_class = MonitorEmailAddressForm

    def form_valid(self, form):

        email_address = form.cleaned_data['email_address']
        LOG.warn('Stage 1: "valid" email address {}'.format(email_address))

        b64_email_address = base64.b64encode(email_address.encode('utf-8'))

        self._create_account_if_not_logged_in(email_address)

        return redirect(
            reverse(
                'users.add-email-confirm-send',
                kwargs={
                    'b64_email_address': b64_email_address
                }
            )
        )

    def _create_account_if_not_logged_in(self, email_address):
        if not self.request.user.is_anonymous():
            return  # already logged in, do nothing

        temp_username = 'tmp-{}'.format(uuid.uuid4())

        with transaction.atomic():
            user = User.objects.create(
                username=temp_username,
            )

            user.set_unusable_password()
            user.save()

            login(self.request, user)
