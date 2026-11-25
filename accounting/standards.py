"""
Financial statement presentation under IFRS and US GAAP.

Both standards are fed from the SAME ledger balances, so profit and total assets are
identical; only the presentation differs:

                       IFRS (IAS 1)                                US GAAP (ASC 205/210/220)
 Statement names       Statement of Financial Position             Balance Sheet
                       Statement of Profit or Loss and OCI         Income Statement
 Asset order           Non-current assets first, then current      Current assets first (liquidity), then non-current
 Equity/Liabilities    Equity first, then non-current liabs,       Liabilities (current, then long-term) first,
                       then current liabilities                    then stockholders' equity
 Income statement      Expenses by NATURE, single-step, with       Expenses by FUNCTION, multi-step: gross profit,
                       finance costs shown separately, then        operating income, other income/expense, net income
                       Other Comprehensive Income
 Profit label          "Profit for the year"                       "Net income"

Accounts are mapped to sections (current / non-current, COGS / operating / finance / tax)
from their code and name - see `classify`.
"""
from decimal import Decimal

from .models import Account

ZERO = Decimal('0')

_CURRENT_ASSET_KW = ('cash', 'bank', 'receivable', 'inventory', 'stock', 'prepaid', 'advance', 'marketable', 'short-term', 'short term')
_NONCURRENT_ASSET_KW = ('building', 'machinery', 'equipment', 'vehicle', 'land', 'furniture', 'plant', 'property', 'intangible',
                        'goodwill', 'accumulated depreciation', 'long-term', 'long term', 'fixed asset', 'patent', 'investment in')
_CURRENT_LIAB_KW = ('payable', 'accrued', 'current', 'short-term', 'short term', 'overdraft', 'unearned', 'deferred revenue', 'tax payable')
_NONCURRENT_LIAB_KW = ('long-term', 'long term', 'mortgage', 'bond', 'debenture', 'deferred tax', 'lease liabilit', 'term loan')
_OTHER_INCOME_KW = ('other income', 'gain', 'interest income', 'interest earned', 'dividend', 'miscellaneous income', 'rental income')
_TAX_KW = ('income tax', 'tax expense', 'provision for tax', 'taxation')
_FINANCE_KW = ('interest', 'finance cost', 'finance charge', 'bank charge', 'bank interest', 'loan charge')
_COGS_KW = ('cost of goods', 'cost of sales', 'cost of revenue', 'cogs', 'inventory write', 'purchases')


def _code_num(account):
    return int(account.code) if account.code.isdigit() else None


def classify(account):
    """Returns the presentation section key for an account."""
    n, code, t = account.name.lower(), _code_num(account), account.account_type
    if t == Account.AccountType.ASSET:
        if any(k in n for k in _CURRENT_ASSET_KW):
            return 'current'
        return 'noncurrent' if (any(k in n for k in _NONCURRENT_ASSET_KW) or (code is not None and code >= 1500)) else 'current'
    if t == Account.AccountType.LIABILITY:
        if any(k in n for k in _NONCURRENT_LIAB_KW):
            return 'noncurrent'
        if any(k in n for k in _CURRENT_LIAB_KW):
            return 'current'
        return 'noncurrent' if (code is not None and code >= 2500) else 'current'
    if t == Account.AccountType.REVENUE:
        return 'other_income' if any(k in n for k in _OTHER_INCOME_KW) else 'revenue'
    if t == Account.AccountType.EXPENSE:
        if any(k in n for k in _TAX_KW):
            return 'tax'
        if any(k in n for k in _FINANCE_KW):
            return 'finance'
        if any(k in n for k in _COGS_KW):
            return 'cogs'
        return 'opex'
    return 'equity'


def _accounts(company):
    return list(Account.objects.filter(company=company)) if company else []


def _rows(accounts, sign=1):
    return [{'name': a.name, 'amount': sign * a.balance} for a in accounts]


def _total(rows):
    return sum((r['amount'] for r in rows), ZERO)


def _section(title, rows):
    return {'title': title, 'rows': rows, 'total': _total(rows)}


def net_profit(company):
    accts = _accounts(company)
    return (sum((-a.balance for a in accts if a.account_type == Account.AccountType.REVENUE), ZERO)
            - sum((a.balance for a in accts if a.account_type == Account.AccountType.EXPENSE), ZERO))


# ------------------------------------------------------------------ Balance sheet
def build_balance_sheet(company):
    ifrs = company.is_ifrs if company else True
    accts = _accounts(company)
    by = lambda t, k=None: [a for a in accts if a.account_type == t and (k is None or classify(a) == k)]
    A, L, E = Account.AccountType.ASSET, Account.AccountType.LIABILITY, Account.AccountType.EQUITY
    profit = net_profit(company) if company else ZERO

    cur_a = _section('Current assets', _rows(by(A, 'current')))
    non_a = _section('Non-current assets', _rows(by(A, 'noncurrent')))
    cur_l = _section('Current liabilities', _rows(by(L, 'current'), -1))
    equity_rows = _rows(by(E), -1) + [{'name': 'Profit for the year' if ifrs else 'Net income (current period)', 'amount': profit}]

    if ifrs:
        non_l = _section('Non-current liabilities', _rows(by(L, 'noncurrent'), -1))
        eq = _section('Equity', equity_rows)
        groups = [
            {'heading': 'ASSETS', 'sections': [non_a, cur_a], 'total_label': 'Total assets',
             'total': non_a['total'] + cur_a['total']},
            {'heading': 'EQUITY AND LIABILITIES', 'sections': [eq, non_l, cur_l], 'total_label': 'Total equity and liabilities',
             'total': eq['total'] + non_l['total'] + cur_l['total']},
        ]
        title, standard_note = 'Statement of Financial Position', (
            'Presented under IFRS (IAS 1): non-current assets are shown before current assets, and equity before liabilities.')
    else:
        lt_l = _section('Long-term liabilities', _rows(by(L, 'noncurrent'), -1))
        liab_total = cur_l['total'] + lt_l['total']
        eq = _section("Stockholders' equity", equity_rows)
        groups = [
            {'heading': 'ASSETS', 'sections': [cur_a, non_a], 'total_label': 'Total assets',
             'total': cur_a['total'] + non_a['total']},
            {'heading': 'LIABILITIES', 'sections': [cur_l, lt_l], 'total_label': 'Total liabilities', 'total': liab_total},
            {'heading': "STOCKHOLDERS' EQUITY", 'sections': [eq], 'total_label': "Total stockholders' equity", 'total': eq['total']},
        ]
        title, standard_note = 'Balance Sheet', (
            'Presented under US GAAP (ASC 210): assets in order of liquidity (current first); liabilities before stockholders\' equity.')

    total_assets = groups[0]['total']
    total_el = sum((g['total'] for g in groups[1:]), ZERO)
    return {
        'title': title, 'standard_note': standard_note, 'groups': groups,
        'grand_total_label': 'Total equity and liabilities' if ifrs else 'Total liabilities and stockholders\' equity',
        'total_assets': total_assets, 'total_equity_liabilities': total_el,
        'balanced': total_assets == total_el,
    }


# ------------------------------------------------------------------ Income statement
def build_income_statement(company):
    """Returns {'title','standard_note','lines':[{kind,label,amount}], 'net_profit'}.
    kind: heading | item | subtotal | total"""
    ifrs = company.is_ifrs if company else True
    accts = _accounts(company)
    R, X = Account.AccountType.REVENUE, Account.AccountType.EXPENSE
    pick = lambda t, k: [a for a in accts if a.account_type == t and classify(a) == k]
    rev = _rows(pick(R, 'revenue'), -1)
    oth = _rows(pick(R, 'other_income'), -1)
    cogs, opex = _rows(pick(X, 'cogs')), _rows(pick(X, 'opex'))
    fin, tax = _rows(pick(X, 'finance')), _rows(pick(X, 'tax'))

    lines = []
    H = lambda label: lines.append({'kind': 'heading', 'label': label, 'amount': None})
    I = lambda rows: lines.extend({'kind': 'item', 'label': r['name'], 'amount': r['amount']} for r in rows)
    S = lambda label, amt: lines.append({'kind': 'subtotal', 'label': label, 'amount': amt})
    T = lambda label, amt: lines.append({'kind': 'total', 'label': label, 'amount': amt})

    if ifrs:
        # single-step, expenses by NATURE (COGS is just another cost line, no gross profit)
        H('Income'); I(rev); I(oth)
        total_income = _total(rev) + _total(oth)
        S('Total income', total_income)
        H('Expenses (by nature)'); I(cogs); I(opex)
        total_exp = _total(cogs) + _total(opex)
        S('Total operating expenses', total_exp)
        op_profit = total_income - total_exp
        S('Operating profit', op_profit)
        H('Finance costs'); I(fin)
        pbt = op_profit - _total(fin)
        S('Profit before tax', pbt)
        H('Income tax expense'); I(tax)
        profit = pbt - _total(tax)
        T('Profit for the year', profit)
        H('Other comprehensive income')
        lines.append({'kind': 'item', 'label': 'No OCI items recorded', 'amount': ZERO})
        T('Total comprehensive income for the year', profit)
        title = 'Statement of Profit or Loss and Other Comprehensive Income'
        note = 'Presented under IFRS (IAS 1): expenses by nature, finance costs shown separately, followed by other comprehensive income.'
    else:
        # multi-step, expenses by FUNCTION
        H('Revenues'); I(rev)
        net_sales = _total(rev)
        S('Net sales', net_sales)
        H('Cost of goods sold'); I(cogs)
        S('Total cost of goods sold', _total(cogs))
        gross = net_sales - _total(cogs)
        S('Gross profit', gross)
        H('Operating expenses'); I(opex)
        S('Total operating expenses', _total(opex))
        op_income = gross - _total(opex)
        S('Operating income', op_income)
        H('Other income and (expenses)')
        I(oth); I([{'name': r['name'], 'amount': -r['amount']} for r in fin])
        other_net = _total(oth) - _total(fin)
        S('Total other income (expense), net', other_net)
        pbt = op_income + other_net
        S('Income before income taxes', pbt)
        H('Income tax expense'); I(tax)
        profit = pbt - _total(tax)
        T('Net income', profit)
        title = 'Income Statement'
        note = 'Presented under US GAAP (ASC 225): multi-step format with gross profit and operating income; expenses by function.'

    return {'title': title, 'standard_note': note, 'lines': lines, 'net_profit': profit}
