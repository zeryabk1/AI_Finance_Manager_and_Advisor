from django import forms
from .models import InventoryItem, StockLot


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        exclude = ['company', 'created_at']

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_sku(self):
        sku = self.cleaned_data['sku']
        if self.company:
            existing = InventoryItem.objects.filter(company=self.company, sku=sku)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f'SKU "{sku}" is already registered for this company. Please use a different SKU.'
                )
        return sku


class StockLotForm(forms.ModelForm):
    """Receive stock: records a purchase layer AND increases the item's on-hand quantity."""
    class Meta:
        model = StockLot
        fields = ['date', 'quantity', 'unit_cost']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_quantity(self):
        qty = self.cleaned_data['quantity']
        if qty <= 0:
            raise forms.ValidationError('Quantity must be greater than zero.')
        return qty
