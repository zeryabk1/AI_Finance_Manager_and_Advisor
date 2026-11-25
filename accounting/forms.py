from django import forms
from .models import Account, JournalEntry


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'account_type']

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_code(self):
        code = self.cleaned_data['code']
        if self.company:
            existing = Account.objects.filter(company=self.company, code=code)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f'Account code "{code}" is already registered for this company. Please use a different code.'
                )
        return code


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['date', 'description', 'debit_account', 'credit_account', 'amount']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['debit_account'].queryset = Account.objects.filter(company=company)
            self.fields['credit_account'].queryset = Account.objects.filter(company=company)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit_account')
        credit = cleaned_data.get('credit_account')
        if debit and credit and debit == credit:
            raise forms.ValidationError('Debit account and Credit account must be different.')
        return cleaned_data
