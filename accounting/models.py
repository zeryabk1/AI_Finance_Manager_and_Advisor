from django.db import models
from django.db.models import Sum
from companies.models import Company


class Account(models.Model):
    """Chart of Accounts."""

    class AccountType(models.TextChoices):
        ASSET = 'ASSET', 'Assets'
        LIABILITY = 'LIABILITY', 'Liabilities'
        EQUITY = 'EQUITY', 'Equity'
        REVENUE = 'REVENUE', 'Revenue'
        EXPENSE = 'EXPENSE', 'Expenses'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        unique_together = ('company', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def balance(self):
        """Running balance = total debits - total credits for this account."""
        debit_total = self.debit_entries.aggregate(total=Sum('amount'))['total'] or 0
        credit_total = self.credit_entries.aggregate(total=Sum('amount'))['total'] or 0
        return debit_total - credit_total


class JournalEntry(models.Model):
    """A journal voucher. Debit total must equal credit total (enforced in the form/view)."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journal_entries')
    date = models.DateField()
    description = models.CharField(max_length=255)
    debit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debit_entries')
    credit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='credit_entries')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"JV-{self.pk}: {self.description} ({self.amount})"
