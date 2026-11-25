from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from companies.models import Company

TWO_PLACES = Decimal('0.01')


def _money(value):
    """Round a Decimal to 2 decimal places (cents) using standard rounding."""
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class FixedAsset(models.Model):
    class DepreciationMethod(models.TextChoices):
        STRAIGHT_LINE = 'STRAIGHT_LINE', 'Straight Line'
        DECLINING_BALANCE = 'DECLINING_BALANCE', 'Declining Balance'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fixed_assets')
    asset_name = models.CharField(max_length=150)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2)
    useful_life_years = models.PositiveIntegerField(help_text='Useful life in years')
    depreciation_method = models.CharField(max_length=20, choices=DepreciationMethod.choices, default=DepreciationMethod.STRAIGHT_LINE)
    salvage_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = ('company', 'asset_name')

    def __str__(self):
        return self.asset_name

    @property
    def annual_depreciation(self):
        if self.useful_life_years == 0:
            return _money(0)
        if self.depreciation_method == self.DepreciationMethod.STRAIGHT_LINE:
            return _money((self.purchase_price - self.salvage_value) / self.useful_life_years)
        # Declining balance: rate = 1 / useful life, applied to current book value
        rate = Decimal(1) / Decimal(self.useful_life_years)
        return _money(self.current_book_value * rate)

    @property
    def years_elapsed(self):
        today = date.today()
        years = today.year - self.purchase_date.year - (
            (today.month, today.day) < (self.purchase_date.month, self.purchase_date.day)
        )
        return max(years, 0)

    @property
    def accumulated_depreciation(self):
        if self.depreciation_method == self.DepreciationMethod.STRAIGHT_LINE:
            annual = (self.purchase_price - self.salvage_value) / self.useful_life_years if self.useful_life_years else Decimal(0)
            years = min(self.years_elapsed, self.useful_life_years)
            return _money(annual * years)
        # Declining balance approximation
        value = self.purchase_price
        rate = Decimal(1) / Decimal(self.useful_life_years) if self.useful_life_years else Decimal(0)
        for _ in range(min(self.years_elapsed, self.useful_life_years)):
            value -= value * rate
        return _money(self.purchase_price - value)

    @property
    def current_book_value(self):
        return _money(max(self.purchase_price - self.accumulated_depreciation, self.salvage_value))
