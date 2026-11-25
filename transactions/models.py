from django.db import models
from companies.models import Company
from inventory.models import InventoryItem


class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class SalesInvoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_invoices')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    invoice_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.pk} - {self.customer.name}"

    @property
    def total(self):
        return sum(line.total for line in self.lines.all())


class SalesInvoiceLine(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def total(self):
        return self.quantity * self.price


class PurchaseBill(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_bills')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='bills')
    purchase_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill #{self.pk} - {self.supplier.name}"

    @property
    def total(self):
        return sum(line.total for line in self.lines.all())


class PurchaseBillLine(models.Model):
    bill = models.ForeignKey(PurchaseBill, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def total(self):
        return self.quantity * self.amount


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK = 'BANK', 'Bank Transfer'
        CARD = 'CARD', 'Card'
        OTHER = 'OTHER', 'Other'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='payments')
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    is_partial = models.BooleanField(default=False)
    date = models.DateField()

    def __str__(self):
        return f"Payment {self.amount} ({self.get_method_display()})"


class Budget(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='budgets')
    year = models.PositiveIntegerField()
    category = models.CharField(max_length=100)
    budget_amount = models.DecimalField(max_digits=14, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.category} {self.year}"

    @property
    def variance(self):
        return self.budget_amount - self.actual_amount
