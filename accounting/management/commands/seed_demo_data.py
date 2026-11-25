"""
Demo data for AI Finance Manager - 6 months of clean, round-number sample data.

Everything is deterministic (no random numbers) and every module posts to the ledger, so the books tie out:
  * Accounts Receivable  = unpaid invoices
  * Accounts Payable     = unpaid bills
  * Inventory (ledger)   = stock on hand x cost
  * Cash / Bank / Inventory never go negative, Balance Sheet balances under IFRS and US GAAP.

Run:   python manage.py seed_demo_data --reset
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from companies.models import Company
from accounting.models import Account, JournalEntry
from inventory.models import InventoryItem, StockLot
from assets.models import FixedAsset
from transactions.models import (
    Customer, Supplier, Budget, SalesInvoice, SalesInvoiceLine,
    PurchaseBill, PurchaseBillLine, Payment,
)

User = get_user_model()


def add_months(d: date, months: int) -> date:
    """Add whole months to a date (first of month), stdlib-only."""
    month_index = d.month - 1 + months
    return date(d.year + month_index // 12, month_index % 12 + 1, 1)


# ---------------------------------------------------------------- fixed demo script
# (sku, name, cost, selling price, opening quantity)
ITEMS = [
    ('ITM-001', 'Office Chair',   3500,  5000,  80),
    ('ITM-002', 'Office Desk',    8000, 12000,  40),
    ('ITM-003', 'Filing Cabinet', 4500,  6500,  30),
    ('ITM-004', 'Whiteboard',     1800,  2800,  40),
    ('ITM-005', 'Desk Lamp',       600,  1000, 150),
]
# Three sales invoices every month: (day of month, [(sku, quantity), ...])
MONTHLY_INVOICES = [
    (3,  [('ITM-002', 12), ('ITM-001', 20)]),
    (12, [('ITM-003', 16), ('ITM-004', 20), ('ITM-005', 60)]),
    (24, [('ITM-001', 24), ('ITM-002', 8), ('ITM-005', 40)]),
]
# Two restocking purchase bills every month: (day of month, [(sku, quantity), ...])
MONTHLY_BILLS = [
    (8,  [('ITM-002', 10), ('ITM-001', 22), ('ITM-003', 8)]),
    (22, [('ITM-002', 10), ('ITM-001', 22), ('ITM-003', 8), ('ITM-004', 20), ('ITM-005', 100)]),
]

# Demo logins - change the passwords HERE (only place). Pick something that is not a common/leaked password,
# otherwise Chrome's password checkup will flag it as "found in a data breach".
DEMO_USERNAME, DEMO_PASSWORD = 'demo', 'HEGY2-28lZ9_97rg'
EMPLOYEE_EMAIL, EMPLOYEE_PASSWORD = 'employee@example.com', 'bHfZv_ACkDG_3zis'

CAPITAL = 3_000_000
LOAN = 500_000
VAN_COST, VAN_SALVAGE, VAN_LIFE = 1_260_000, 60_000, 5            # 20,000 / month
COMPUTER_COST, COMPUTER_SALVAGE, COMPUTER_LIFE = 300_000, 12_000, 3  # 8,000 / month
PETTY_CASH = 100_000
RENT, UTILITIES, OFFICE, SALARIES = 30_000, 8_000, 5_000, 60_000
LOAN_INTEREST, TAX_PROVISION, CASH_DEPOSIT = 5_000, 10_000, 150_000
DEPRECIATION = (VAN_COST - VAN_SALVAGE) // (VAN_LIFE * 12) + (COMPUTER_COST - COMPUTER_SALVAGE) // (COMPUTER_LIFE * 12)


class Command(BaseCommand):
    help = 'Creates a demo user, company and 6 months of clean sample data across every module.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete existing demo company data before regenerating it.')

    def handle(self, *args, **options):
        today = date.today()
        start_month = add_months(today.replace(day=1), -5)   # 6 months, last one = current month
        day = lambda month_idx, n: add_months(start_month, month_idx).replace(day=n)

        # ------------------------------------------------------------ users
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME, defaults={'email': 'demo@example.com', 'role': User.Role.COMPANY_OWNER})
        user.set_password(DEMO_PASSWORD)     # always (re)set, so re-running the seed refreshes the demo login
        user.save()
        employee, employee_created = User.objects.get_or_create(
            email=EMPLOYEE_EMAIL, defaults={'username': EMPLOYEE_EMAIL, 'role': User.Role.EMPLOYEE})
        employee.set_password(EMPLOYEE_PASSWORD)
        employee.save()

        # ------------------------------------------------------------ company
        company, company_created = Company.objects.get_or_create(
            owner=user, name='Demo Traders Pvt Ltd',
            defaults={'country': 'Pakistan', 'currency': 'PKR', 'fiscal_year_start': date(today.year, 1, 1),
                      'accounting_standard': 'IFRS', 'inventory_method': 'FIFO'},
        )
        company.staff.add(employee)

        if options['reset'] and not company_created:
            self.stdout.write('Resetting existing demo data for this company...')
            SalesInvoice.objects.filter(company=company).delete()
            PurchaseBill.objects.filter(company=company).delete()
            Payment.objects.filter(company=company).delete()
            JournalEntry.objects.filter(company=company).delete()
            Budget.objects.filter(company=company).delete()
            InventoryItem.objects.filter(company=company).delete()
            Customer.objects.filter(company=company).delete()
            Supplier.objects.filter(company=company).delete()
            FixedAsset.objects.filter(company=company).delete()
            Account.objects.filter(company=company).delete()

        if JournalEntry.objects.filter(company=company).exists() or SalesInvoice.objects.filter(company=company).exists():
            self.stdout.write(self.style.WARNING('Demo data already exists. Run with --reset to rebuild it.'))
            return

        # ------------------------------------------------------------ chart of accounts
        T = Account.AccountType
        chart = [
            ('1000', 'Cash in Hand', T.ASSET), ('1010', 'Bank Account', T.ASSET),
            ('1100', 'Accounts Receivable', T.ASSET), ('1200', 'Inventory', T.ASSET),
            ('1300', 'Prepaid Expenses', T.ASSET), ('1500', 'Land & Building', T.ASSET),
            ('1510', 'Machinery & Equipment', T.ASSET), ('1520', 'Furniture & Fixtures', T.ASSET),
            ('1530', 'Vehicles', T.ASSET), ('1590', 'Accumulated Depreciation', T.ASSET),
            ('2000', 'Accounts Payable', T.LIABILITY), ('2100', 'Accrued Expenses', T.LIABILITY),
            ('2200', 'Salaries Payable', T.LIABILITY), ('2300', 'Income Tax Payable', T.LIABILITY),
            ('2600', 'Long-term Loan', T.LIABILITY),
            ('3000', "Owner's Capital", T.EQUITY), ('3100', 'Retained Earnings', T.EQUITY),
            ('4000', 'Sales Revenue', T.REVENUE), ('4100', 'Other Income', T.REVENUE),
            ('5000', 'Cost of Goods Sold', T.EXPENSE), ('5100', 'Rent Expense', T.EXPENSE),
            ('5200', 'Utilities Expense', T.EXPENSE), ('5300', 'Salaries Expense', T.EXPENSE),
            ('5400', 'Office Expenses', T.EXPENSE), ('5500', 'Depreciation Expense', T.EXPENSE),
            ('5600', 'Interest Expense', T.EXPENSE), ('5700', 'Income Tax Expense', T.EXPENSE),
        ]
        accounts = {code: Account.objects.get_or_create(company=company, code=code,
                                                        defaults={'name': name, 'account_type': t})[0]
                    for code, name, t in chart}

        # ------------------------------------------------------------ customers, suppliers, items
        customers = [Customer.objects.create(company=company, name=n, phone=f'0300-{1000000 + i:07d}',
                                             email=f'{n.split()[0].lower()}@example.com')
                     for i, n in enumerate(['Ali Traders', 'Khan Enterprises', 'Zainab Retail', 'Metro Mart', 'City Hardware'])]
        suppliers = [Supplier.objects.create(company=company, name=n, phone=f'021-{2000000 + i:07d}',
                                             email=f'{n.split()[0].lower()}@example.com')
                     for i, n in enumerate(['Karachi Wholesalers', 'Lahore Textiles Co', 'Punjab Supplies'])]
        items = {}
        for sku, name, cost, sell, qty in ITEMS:
            items[sku] = InventoryItem.objects.create(
                company=company, sku=sku, item_name=name, quantity=qty, unit_price=sell,
                cost_price=cost, selling_price=sell, low_stock_threshold=10)
            StockLot.objects.create(item=items[sku], date=start_month, quantity=qty, unit_cost=cost)   # opening layer

        entries = []   # (date, description, debit_code, credit_code, amount)
        E = lambda d, desc, dr, cr, amt: entries.append((d, desc, dr, cr, Decimal(amt)))
        opening_stock_value = sum(i[2] * i[4] for i in ITEMS)

        # ------------------------------------------------------------ opening position (first days of the first month)
        E(day(0, 1), "Owner invested capital", '1010', '3000', CAPITAL)
        E(day(0, 1), 'Bank loan received', '1010', '2600', LOAN)
        E(day(0, 2), 'Purchased delivery van', '1530', '1010', VAN_COST)
        E(day(0, 2), 'Purchased office computers', '1510', '1010', COMPUTER_COST)
        E(day(0, 2), 'Opening stock purchased', '1200', '1010', opening_stock_value)
        E(day(0, 3), 'Cash withdrawn from bank (petty cash)', '1000', '1010', PETTY_CASH)

        # ------------------------------------------------------------ sales invoices, customer payments, cost of goods sold
        n_inv = 0
        for m in range(6):
            for k, (d_num, lines) in enumerate(MONTHLY_INVOICES):
                inv_date = day(m, d_num)
                if inv_date > today:
                    continue
                customer = customers[n_inv % len(customers)]
                n_inv += 1
                invoice = SalesInvoice.objects.create(company=company, customer=customer, invoice_date=inv_date)
                cost = Decimal(0)
                for sku, qty in lines:
                    it = items[sku]
                    SalesInvoiceLine.objects.create(invoice=invoice, item=it, quantity=qty, price=it.selling_price)
                    it.quantity -= qty
                    cost += qty * it.cost_price
                total = invoice.total
                E(inv_date, f'Credit sale to {customer.name} (Invoice #{invoice.pk})', '1100', '4000', total)
                E(inv_date, f'Cost of goods sold (Invoice #{invoice.pk})', '5000', '1200', cost)

                recent = (today - inv_date).days <= 30     # recent invoices stay (partly) unpaid
                if k == 0:                                  # invoice 1: paid in full by bank transfer
                    pay, method, lag, partial = total, Payment.Method.BANK, 2, False
                elif k == 1:                                # invoice 2: paid in cash (half only if still recent)
                    pay, method, lag, partial = (total / 2 if recent else total), Payment.Method.CASH, 1, recent
                else:                                       # invoice 3: paid by bank, unless still recent
                    pay, method, lag, partial = (None if recent else total), Payment.Method.BANK, 5, False
                if pay:
                    pay_date = min(inv_date + timedelta(days=lag), today)
                    Payment.objects.create(company=company, invoice=invoice, amount=pay, method=method,
                                           is_partial=partial, date=pay_date)
                    label = 'Cash' if method == Payment.Method.CASH else 'Bank'
                    E(pay_date, f'Payment received from {customer.name} - Invoice #{invoice.pk} ({label})',
                      '1000' if method == Payment.Method.CASH else '1010', '1100', pay)

        # ------------------------------------------------------------ purchase bills (restocking) and supplier payments
        n_bill = 0
        for m in range(6):
            for d_num, lines in MONTHLY_BILLS:
                bill_date = day(m, d_num)
                if bill_date > today:
                    continue
                supplier = suppliers[n_bill % len(suppliers)]
                n_bill += 1
                bill = PurchaseBill.objects.create(company=company, supplier=supplier, purchase_date=bill_date)
                for sku, qty in lines:
                    it = items[sku]
                    PurchaseBillLine.objects.create(bill=bill, item=it, quantity=qty, amount=it.cost_price)
                    it.quantity += qty
                    StockLot.objects.create(item=it, date=bill_date, quantity=qty, unit_cost=it.cost_price)
                E(bill_date, f'Purchase from {supplier.name} (Bill #{bill.pk})', '1200', '2000', bill.total)
                pay_date = bill_date + timedelta(days=10)
                if pay_date <= today:
                    E(pay_date, f'Paid to {supplier.name} (Bill #{bill.pk})', '2000', '1010', bill.total)

        for it in items.values():           # stock on hand now = opening + bills - sold
            it.save(update_fields=['quantity'])

        # ------------------------------------------------------------ monthly overheads
        for m in range(6):
            if day(m, 5) <= today:
                E(day(m, 5), 'Monthly rent paid', '5100', '1010', RENT)
            if day(m, 7) <= today:
                E(day(m, 7), 'Utility bills paid', '5200', '1000', UTILITIES)
            if day(m, 10) <= today:
                E(day(m, 10), 'Office supplies purchased', '5400', '1000', OFFICE)
            if day(m, 26) <= today:
                E(day(m, 26), 'Cash deposited to bank', '1010', '1000', CASH_DEPOSIT)
            if day(m, 28) <= today:
                E(day(m, 28), 'Staff salaries paid', '5300', '1010', SALARIES)
                E(day(m, 28), 'Monthly depreciation (van + computers)', '5500', '1590', DEPRECIATION)
                E(day(m, 28), 'Loan interest paid', '5600', '1010', LOAN_INTEREST)
                E(day(m, 28), 'Income tax provision', '5700', '2300', TAX_PROVISION)

        entries.sort(key=lambda e: e[0])     # stable: same-day entries keep the order above
        for entry_date, desc, dr, cr, amount in entries:
            JournalEntry.objects.create(company=company, date=entry_date, description=desc,
                                        debit_account=accounts[dr], credit_account=accounts[cr], amount=amount)

        # ------------------------------------------------------------ fixed assets register (same figures as the ledger)
        FixedAsset.objects.create(
            company=company, asset_name='Delivery Van', purchase_date=start_month, purchase_price=VAN_COST,
            useful_life_years=VAN_LIFE, salvage_value=VAN_SALVAGE,
            depreciation_method=FixedAsset.DepreciationMethod.STRAIGHT_LINE)
        FixedAsset.objects.create(
            company=company, asset_name='Office Computers', purchase_date=start_month, purchase_price=COMPUTER_COST,
            useful_life_years=COMPUTER_LIFE, salvage_value=COMPUTER_SALVAGE,
            depreciation_method=FixedAsset.DepreciationMethod.STRAIGHT_LINE)

        # ------------------------------------------------------------ budgets
        for m in range(6):
            ms = add_months(start_month, m)
            Budget.objects.create(company=company, year=ms.year, category=f'Office Expenses ({ms.strftime("%b")})',
                                  budget_amount=15000, actual_amount=OFFICE + UTILITIES)
            Budget.objects.create(company=company, year=ms.year, category=f'Salaries ({ms.strftime("%b")})',
                                  budget_amount=65000, actual_amount=SALARIES)

        self.stdout.write(self.style.SUCCESS(
            f'Created {n_inv} sales invoices, {n_bill} purchase bills and {len(entries)} journal entries '
            f'({start_month.strftime("%b %Y")} -> {today.strftime("%b %Y")}).'))
        self.stdout.write(self.style.SUCCESS(f'  Owner login:    {DEMO_USERNAME} / {DEMO_PASSWORD}'))
        self.stdout.write(self.style.SUCCESS(f'  Employee login: {EMPLOYEE_EMAIL} / {EMPLOYEE_PASSWORD}'))