from django.db import models
from companies.models import Company


class InventoryItem(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory_items')
    item_name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    selling_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Estimated cost to sell one unit (commission, delivery...). Used for Net Realisable Value.',
    )
    # Total write-down already posted to the ledger for this item (see inventory/valuation.py).
    recorded_writedown = models.DecimalField(max_digits=14, decimal_places=2, default=0, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'sku')
        ordering = ['item_name']

    def __str__(self):
        return f"{self.item_name} ({self.sku})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    @property
    def stock_value(self):
        return self.quantity * self.cost_price


class StockLot(models.Model):
    """One purchase layer (date, quantity, unit cost). On-hand stock is costed from these layers."""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='lots')
    date = models.DateField()
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'id']

    def __str__(self):
        return f"{self.item.item_name}: {self.quantity} @ {self.unit_cost} ({self.date})"
