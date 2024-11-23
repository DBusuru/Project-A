from .models import CustomUser as User
from django import forms
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text='Enter any password you like'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput,
        help_text='Enter the same password as above'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def _post_clean(self):
        super(forms.ModelForm, self)._post_clean()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                "The two password fields didn't match.",
                code='password_mismatch',
            )
        return password2
