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

class UserProfileForm(forms.ModelForm):
    link1 = forms.URLField(required=False, label='Social Link 1')
    link2 = forms.URLField(required=False, label='Social Link 2')
    link3 = forms.URLField(required=False, label='Social Link 3')
    link4 = forms.URLField(required=False, label='Social Link 4')
    link5 = forms.URLField(required=False, label='Social Link 5')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'profile_picture', 'school', 'link1', 'link2', 'link3', 'link4', 'link5']

    def clean(self):
        cleaned_data = super().clean()
        social_links = {
            'link1': cleaned_data.get('link1'),
            'link2': cleaned_data.get('link2'),
            'link3': cleaned_data.get('link3'),
            'link4': cleaned_data.get('link4'),
            'link5': cleaned_data.get('link5'),
        }
        cleaned_data['social_links'] = {key: value for key, value in social_links.items() if value}
        return cleaned_data