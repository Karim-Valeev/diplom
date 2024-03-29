from django import forms
from django.contrib.auth.forms import UserCreationForm

from app.models import User, Video


class LoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField()


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ('title', 'file')
