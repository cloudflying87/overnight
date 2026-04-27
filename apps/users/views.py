from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    ProfileUpdateForm,
    CustomPasswordChangeForm,
    SettingsForm
)


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


@login_required
def profile_view(request):
    """User profile page - update display name, email, and password"""
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('users:profile')
        elif 'change_password' in request.POST:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('users:profile')
        else:
            profile_form = ProfileUpdateForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)
    else:
        profile_form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'users/profile.html', context)


@login_required
def settings_view(request):
    """User settings page - timezone and preferences"""
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('users:settings')
    else:
        form = SettingsForm(instance=request.user)

    context = {
        'form': form,
    }
    return render(request, 'users/settings.html', context)
