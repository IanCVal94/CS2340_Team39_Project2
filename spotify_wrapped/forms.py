"""
Forms for handling user registration with an additional email field.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):  # pylint: disable=too-many-ancestors, too-few-public-methods
    """
    Form for registering a new user, extending Django's UserCreationForm
    to include an email field along with the standard username and password fields.
    """
    email = forms.EmailField()

    class Meta:
        """
        Metaclass to specify the model and fields to be used in the form.
        """
        model = User
        fields = ['username', 'email', 'password1', 'password2']
