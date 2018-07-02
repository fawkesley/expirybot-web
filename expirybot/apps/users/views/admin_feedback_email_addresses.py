from django.views.generic import TemplateView
from ..models import UserProfile

from expirybot.apps.users.utils import make_authenticated_one_click_config_url


class AdminFeedbackEmailAddressesView(TemplateView):
    template_name = 'users/admin_feedback_email_addresses.html'
    queryset = UserProfile.objects.filter(
        receive_occasional_feedback_requests=True
    ).prefetch_related('email_address_ownership_proofs__email_address')

    context_object_name = 'user_profiles'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        def make_users():
            profiles = UserProfile.objects.filter(
                receive_occasional_feedback_requests=True
            ).prefetch_related('user')

            for profile in profiles:
                yield {
                    'email_address': profile.user.email,
                    'opt_out_url': make_authenticated_one_click_config_url(
                        profile,
                        'receive_occasional_feedback_requests',
                        False
                    )
                }

        ctx['users'] = make_users()
        return ctx
