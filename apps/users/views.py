from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, CustomAuthenticationForm


class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('care_tracking:dashboard')


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = 'users:login'


class SignUpView(CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        """Auto-login user after successful registration and create default event options"""
        response = super().form_valid(form)
        user = form.save()

        # Create default event options for the new user
        from apps.care_tracking.utils import create_default_event_options
        create_default_event_options(user)

        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('care_tracking:dashboard')
