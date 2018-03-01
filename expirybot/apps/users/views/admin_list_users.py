from django.views.generic import ListView
from ..models import UserProfile


class AdminListUsers(ListView):
    template_name = 'users/admin_list_users.html'
    queryset = UserProfile.objects.all().prefetch_related('email_address_ownership_proofs__email_address')
    context_object_name = 'user_profiles'
