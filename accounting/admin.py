from django.contrib import admin
from .models import Account, JournalEntry


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'company')
    list_filter = ('account_type', 'company')
    search_fields = ('code', 'name')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'date', 'description', 'debit_account', 'credit_account', 'amount', 'company')
    list_filter = ('company', 'date')
