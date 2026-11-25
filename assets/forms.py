from django import forms
from .models import FixedAsset


class FixedAssetForm(forms.ModelForm):
    class Meta:
        model = FixedAsset
        exclude = ['company']
        widgets = {'purchase_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_asset_name(self):
        asset_name = self.cleaned_data['asset_name']
        if self.company:
            existing = FixedAsset.objects.filter(company=self.company, asset_name=asset_name)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f'An asset named "{asset_name}" is already registered for this company. Please use a different name (e.g. add a tag number, like "Delivery Van #2").'
                )
        return asset_name
