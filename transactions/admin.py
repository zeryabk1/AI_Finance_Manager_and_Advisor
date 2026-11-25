from django.contrib import admin
from .models import (
    Customer, Supplier, SalesInvoice, SalesInvoiceLine,
    PurchaseBill, PurchaseBillLine, Payment, Budget,
)


class SalesInvoiceLineInline(admin.TabularInline):
    model = SalesInvoiceLine
    extra = 1


class PurchaseBillLineInline(admin.TabularInline):
    model = PurchaseBillLine
    extra = 1


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'company')
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'company')
    search_fields = ('name',)


@admin.register(SalesInvoice)
class SalesInvoiceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'customer', 'invoice_date', 'total', 'company')
    inlines = [SalesInvoiceLineInline]


@admin.register(PurchaseBill)
class PurchaseBillAdmin(admin.ModelAdmin):
    list_display = ('pk', 'supplier', 'purchase_date', 'total', 'company')
    inlines = [PurchaseBillLineInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'invoice', 'amount', 'method', 'is_partial', 'date', 'company')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'year', 'budget_amount', 'actual_amount', 'variance', 'company')
