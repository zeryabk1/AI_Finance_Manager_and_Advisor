"""
Shared ledger logic used by the General Ledger page and its PDF / Excel exports,
so all three always show exactly the same numbers.

Balances are shown the way accountants normally write them: an absolute amount
followed by Dr (debit balance) or Cr (credit balance).  Nothing is ever shown
with a minus sign.  If an account ends up on the side opposite to its normal
side (e.g. Inventory with a Cr balance), `unusual` is True so the page can warn
the user - that usually means a purchase / opening entry is missing.
"""
from decimal import Decimal

CREDIT_NORMAL_TYPES = {'LIABILITY', 'EQUITY', 'REVENUE'}   # everything else is debit-normal
# Contra-assets are ASSET accounts that normally carry a CREDIT balance (e.g. Accumulated Depreciation).
CONTRA_ASSET_KEYWORDS = ('accumulated depreciation', 'accumulated amortization', 'accumulated amortisation',
                         'allowance for', 'provision for doubtful')


def is_credit_normal(account):
    n = account.name.lower()
    return account.account_type in CREDIT_NORMAL_TYPES or any(k in n for k in CONTRA_ASSET_KEYWORDS)


def _side(raw):
    """raw = debits - credits.  Returns 'Dr', 'Cr' or ''."""
    if raw > 0:
        return 'Dr'
    if raw < 0:
        return 'Cr'
    return ''


def build_ledger(account):
    """Returns {'entries': [...], 'closing': {...}, 'normal_side': 'Dr'|'Cr'}."""
    normal_side = 'Cr' if is_credit_normal(account) else 'Dr'

    combined = sorted(
        [(e, 'DEBIT') for e in account.debit_entries.all()] +
        [(e, 'CREDIT') for e in account.credit_entries.all()],
        key=lambda x: (x[0].date, x[0].created_at, x[0].pk),
    )

    raw = Decimal('0')
    entries = []
    for e, kind in combined:
        raw += e.amount if kind == 'DEBIT' else -e.amount
        entries.append({
            'date': e.date,
            'journal_no': e.pk,
            'description': e.description,
            'debit': e.amount if kind == 'DEBIT' else None,
            'credit': e.amount if kind == 'CREDIT' else None,
            'balance': abs(raw),
            'side': _side(raw),
        })

    side = _side(raw)
    closing = {
        'balance': abs(raw),
        'side': side,
        'unusual': bool(side) and side != normal_side,
    }
    return {'entries': entries, 'closing': closing, 'normal_side': normal_side}
