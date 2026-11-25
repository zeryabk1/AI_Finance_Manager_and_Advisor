from django import forms
from .models import (
    Customer, Supplier, Budget, SalesInvoice, SalesInvoiceLine,
    PurchaseBill, PurchaseBillLine, Payment,
)


class BaseStyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class CustomerForm(BaseStyledForm):
    class Meta:
        model = Customer
        exclude = ['company']


class SupplierForm(BaseStyledForm):
    class Meta:
        model = Supplier
        exclude = ['company']


class BudgetForm(BaseStyledForm):
    class Meta:
        model = Budget
        exclude = ['company']


class SalesInvoiceForm(BaseStyledForm):
    class Meta:
        model = SalesInvoice
        fields = ['customer', 'invoice_date']
        widgets = {'invoice_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = Customer.objects.filter(company=company)


SalesInvoiceLineFormSet = forms.inlineformset_factory(
    SalesInvoice, SalesInvoiceLine,
    fields=['item', 'quantity', 'price'],
    extra=3, can_delete=True,
)


class PurchaseBillForm(BaseStyledForm):
    class Meta:
        model = PurchaseBill
        fields = ['supplier', 'purchase_date']
        widgets = {'purchase_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['supplier'].queryset = Supplier.objects.filter(company=company)


PurchaseBillLineFormSet = forms.inlineformset_factory(
    PurchaseBill, PurchaseBillLine,
    fields=['item', 'quantity', 'amount'],
    extra=3, can_delete=True,
)


class PaymentForm(BaseStyledForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'method', 'is_partial', 'date']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['invoice'].queryset = SalesInvoice.objects.filter(company=company)
