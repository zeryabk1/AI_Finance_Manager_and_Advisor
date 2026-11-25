from django.contrib import admin
from .models import FixedAsset


@admin.register(FixedAsset)
class FixedAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_name', 'company', 'purchase_date', 'purchase_price', 'depreciation_method', 'current_book_value')
    list_filter = ('company', 'depreciation_method')
