from django.views.generic import ListView
from ..models import UserProfile


class AdminAllEmailAddressesView(ListView):
    template_name = 'users/admin_all_email_addresses.html'
    queryset = UserProfile.objects.all().prefetch_related('email_address_ownership_proofs__email_address')
    context_object_name = 'user_profiles'
