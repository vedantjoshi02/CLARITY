from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import redirect
from django.urls import reverse_lazy


class StudentPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        return (
            user for user in super().get_users(email)
            if not user.is_staff and not user.is_superuser and hasattr(user, 'profile')
        )


class StudentPasswordReset(auth_views.PasswordResetView):
    form_class = StudentPasswordResetForm
    template_name = 'academy/password_reset_page.html'
    email_template_name = 'academy/password_reset_email.txt'
    subject_template_name = 'academy/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def post(self, request, *args, **kwargs):
        from .views import limited
        address = request.META.get('REMOTE_ADDR', '')
        email = request.POST.get('email', '').strip().casefold()[:254]
        if limited(f'reset:ip:{address}', 10, 3600):
            return redirect(self.success_url)
        if email and limited(f'reset:email:{email}', 3, 3600):
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        public_url = settings.PUBLIC_BASE_URL
        if not public_url:
            if settings.DEBUG:
                return super().form_valid(form)
            return redirect(self.success_url)

        url = urlsplit(public_url)
        if (url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password
                or url.path or url.query or url.fragment or (not settings.DEBUG and url.scheme != 'https')):
            return redirect(self.success_url)
        form.save(
            domain_override=url.netloc, use_https=url.scheme == 'https',
            token_generator=self.token_generator, from_email=self.from_email,
            email_template_name=self.email_template_name,
            subject_template_name=self.subject_template_name,
        )
        return redirect(self.success_url)
