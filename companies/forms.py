from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Company

User = get_user_model()


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude = ['owner', 'staff', 'created_at']
        widgets = {
            'fiscal_year_start': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'logo':
                field.widget.attrs.update({'class': 'form-control'})


class CreateStaffForm(forms.Form):
    """
    Used by a Company Owner to create an Accountant or Employee account
    for their company in one step. The staff member then logs in with
    just this email + password (see accounts/backends.py).

    If the email already belongs to an existing Accountant/Employee
    account (e.g. one already used on another company), this form
    simply grants that existing account access instead of creating a
    duplicate — password/role fields are ignored in that case.
    """
    full_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'employee@example.com'}),
    )
    role = forms.ChoiceField(
        choices=[(User.Role.EMPLOYEE, 'Employee'), (User.Role.ACCOUNTANT, 'Accountant')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if this email already has an account'}),
        help_text='Required only when creating a brand-new account for this email.',
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if not email:
            return cleaned_data

        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            if existing.role not in (User.Role.ACCOUNTANT, User.Role.EMPLOYEE):
                raise ValidationError('That email belongs to a Company Owner or Super Admin account, and cannot be added as staff.')
        else:
            if not password:
                raise ValidationError('This email has no existing account yet — please set a password to create one.')
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data
