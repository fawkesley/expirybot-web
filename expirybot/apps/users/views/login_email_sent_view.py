from django.views.generic import TemplateView


class LoginEmailSentView(TemplateView):
    template_name = 'users/login_email_sent.html'
