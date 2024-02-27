from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView, LoginView as DjangoLoginView
from django.urls import reverse_lazy
from django.views.generic import TemplateView


# from app.forms import CustomAuthenticationForm


class MainPageView(TemplateView):
    template_name = "main.html"


class LoginView(DjangoLoginView):
    # form_class = CustomAuthenticationForm
    template_name = "login.html"
    # authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = False


class LogoutView(LoginRequiredMixin, DjangoLogoutView):
    next_page = reverse_lazy("login")


class UserListView():
    pass


class UserDetailView():
    pass
