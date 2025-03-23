from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from .forms import UserRegistrationForm, UserLoginForm

class RegisterView(FormView):
    template_name = "register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("game:home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = "login.html"
    success_url = reverse_lazy("game:home")
    redirect_authenticated_user = True
    authentication_form = UserLoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")
        if not remember_me:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")
