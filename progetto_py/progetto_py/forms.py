from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import User
from django import forms


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class FormThingCreation(forms.Form):
    name_park = forms.CharField(max_length=50, min_length=5, label='Name of the Thing')

