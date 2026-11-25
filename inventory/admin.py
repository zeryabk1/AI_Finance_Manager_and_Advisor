from django.contrib import admin
from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'sku', 'company', 'quantity', 'unit_price', 'selling_price', 'is_low_stock')
    list_filter = ('company',)
    search_fields = ('item_name', 'sku')
