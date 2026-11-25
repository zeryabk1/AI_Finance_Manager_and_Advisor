from django.conf import settings
from django.db import models


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    currency = models.CharField(max_length=10, default='USD')
    fiscal_year_start = models.DateField()
    class Standard(models.TextChoices):
        IFRS = 'IFRS', 'IFRS'
        GAAP = 'GAAP', 'US GAAP'

    class InventoryMethod(models.TextChoices):
        FIFO = 'FIFO', 'FIFO (First-In, First-Out)'
        LIFO = 'LIFO', 'LIFO (Last-In, First-Out) - US GAAP only'
        WAC = 'WAC', 'Weighted Average Cost'

    accounting_standard = models.CharField(
        max_length=20, choices=Standard.choices, default=Standard.IFRS,
        help_text='Controls how inventory is valued and how the Balance Sheet / Income Statement are presented.',
    )
    inventory_method = models.CharField(
        max_length=10, choices=InventoryMethod.choices, default=InventoryMethod.FIFO,
        help_text='Cost-flow method. LIFO is prohibited under IFRS (IAS 2).',
    )
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Staff members (Accountants/Employees) the owner has granted access to this company.
    # Their global role (accounts.User.role) still governs what they're allowed to do.
    staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='member_companies',
        help_text='Accountants/Employees granted access to this company.',
    )

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.accounting_standard == self.Standard.IFRS and self.inventory_method == self.InventoryMethod.LIFO:
            raise ValidationError({'inventory_method': 'LIFO is not permitted under IFRS (IAS 2). '
                                                       'Choose FIFO or Weighted Average, or switch the standard to US GAAP.'})

    @property
    def is_ifrs(self):
        return self.accounting_standard != self.Standard.GAAP

    @property
    def standard_label(self):
        return 'IFRS' if self.is_ifrs else 'US GAAP'

    def user_has_access(self, user):
        if user.is_authenticated and getattr(user, 'is_super_admin', False):
            return True
        return user == self.owner or self.staff.filter(pk=user.pk).exists()
