from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.contrib.auth.forms import AuthenticationForm

class BaseRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class ProfesorRegisterForm(BaseRegisterForm):
    is_profesor = forms.BooleanField(initial=True, widget=forms.HiddenInput)  # Hidden field
    school = forms.CharField(max_length=255, required=True)

    class Meta(BaseRegisterForm.Meta):
        fields = BaseRegisterForm.Meta.fields + ['is_profesor', 'school']

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(CustomAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Adresa dvs.'
        self.fields['password'].widget.attrs['placeholder'] = 'Parola dvs.'