from app.forms import LoginForm, RegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView


class MainPageView(TemplateView):
    template_name = 'main.html'


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        request = self.request
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, email=email, password=password)
        if user is None:
            form.add_error('email', 'Неправильный логин или пароль')
        else:
            login(request, user)
            return redirect('profile')
        return render(request, 'login.html', {'form': form})


class LogoutView(LoginRequiredMixin, DjangoLogoutView):
    next_page = reverse_lazy('main')


class UserCreateView(CreateView):
    form_class = RegistrationForm
    template_name = 'registration.html'
    success_url = reverse_lazy('login')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
