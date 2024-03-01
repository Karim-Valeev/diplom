from app.models import User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class LoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField()


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
