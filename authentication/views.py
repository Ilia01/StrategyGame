from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from .forms import UserRegistrationForm, UserLoginForm

class RegisterView(FormView):
    template_name = "register.html"
    form_class = UserRegistrationForm

    def get_success_url(self):
        return reverse_lazy("game:home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Account created successfully!")
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = "login.html"
    authentication_form = UserLoginForm

    def get_success_url(self):
        return reverse_lazy("game:home")

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('auth:login')
