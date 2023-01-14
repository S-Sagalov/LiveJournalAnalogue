from django.shortcuts import render
from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm)
from django.contrib.auth.views import (PasswordChangeView, PasswordResetView,
                                       PasswordResetConfirmView)
from django.views.generic import CreateView, View
from django.urls import reverse_lazy

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordsChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'


class PasswordChangeDoneView(View):
    template_name = 'users/change_accepted/password_change_done.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class PasswordsResetView(PasswordResetView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset_form.html'


class PasswordResetDoneView(View):
    template_name = 'users/change_accepted/password_reset_done.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class PasswordsResetConfirmView(PasswordResetConfirmView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('users:reset_done')
    template_name = 'users/password_reset_confirm.html'


class PasswordResetCompleteView(View):
    template_name = 'users/change_accepted/password_reset_complete.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
