"""
business_stability.py
----------------------
Calculates the Business Stability Index (0-100) from a company's live
Chart of Accounts data. This is a rule-based scoring engine (not a
trained model) because these financial ratios have well-established
industry formulas — the "AI" value-add here is combining six ratios
into one weighted, explainable score with a status label.

Usage (see reports/views.py):
    from ai_models.business_stability import calculate_stability_index
    result = calculate_stability_index(company)
"""
from django.db.models import Sum
from accounting.models import Account


def _sum_balances(accounts):
    return sum(a.balance for a in accounts)


def calculate_stability_index(company):
    accounts = Account.objects.filter(company=company)

    assets = accounts.filter(account_type=Account.AccountType.ASSET)
    liabilities = accounts.filter(account_type=Account.AccountType.LIABILITY)
    revenue = accounts.filter(account_type=Account.AccountType.REVENUE)
    expenses = accounts.filter(account_type=Account.AccountType.EXPENSE)

    total_assets = float(_sum_balances(assets))
    total_liabilities = float(-_sum_balances(liabilities))  # liabilities carry credit balances
    total_revenue = float(-_sum_balances(revenue))          # revenue carries credit balance
    total_expenses = float(_sum_balances(expenses))

    # Treat "Cash" style accounts as liquid assets (simple heuristic: account name contains 'cash' or 'bank')
    liquid_accounts = assets.filter(name__icontains='cash') | assets.filter(name__icontains='bank')
    liquid_assets = float(_sum_balances(liquid_accounts.distinct()))

    net_profit = total_revenue - total_expenses

    # --- Individual ratio scores (each scaled 0-100) ---
    # Liquidity: liquid assets vs liabilities (current ratio style)
    liquidity_score = 100 if total_liabilities == 0 else min(100, (liquid_assets / total_liabilities) * 50)
    liquidity_score = max(0, liquidity_score)

    # Profitability: net profit margin
    profitability_score = 50 if total_revenue == 0 else max(0, min(100, (net_profit / total_revenue) * 100 + 50))

    # Cash flow score: liquid assets relative to total expenses (runway proxy)
    cash_flow_score = 100 if total_expenses == 0 else max(0, min(100, (liquid_assets / total_expenses) * 40))

    # Revenue growth: not enough historical data yet without period-over-period tracking,
    # so we default to a neutral 50 unless revenue is clearly zero.
    revenue_growth_score = 50 if total_revenue > 0 else 20

    # Expense control: expenses as a proportion of revenue (lower is better)
    expense_control_score = 100 if total_revenue == 0 else max(0, min(100, 100 - (total_expenses / total_revenue) * 100))

    # Debt ratio: liabilities vs assets (lower is better)
    debt_ratio_score = 100 if total_assets == 0 else max(0, min(100, 100 - (total_liabilities / total_assets) * 100))

    weights = {
        'liquidity': 0.20,
        'profitability': 0.20,
        'cash_flow': 0.20,
        'revenue_growth': 0.10,
        'expense_control': 0.15,
        'debt_ratio': 0.15,
    }
    scores = {
        'liquidity': liquidity_score,
        'profitability': profitability_score,
        'cash_flow': cash_flow_score,
        'revenue_growth': revenue_growth_score,
        'expense_control': expense_control_score,
        'debt_ratio': debt_ratio_score,
    }

    stability_score = sum(scores[k] * weights[k] for k in weights)
    stability_score = round(max(0, min(100, stability_score)), 1)

    if stability_score >= 80:
        status = 'Excellent'
    elif stability_score >= 60:
        status = 'Good'
    elif stability_score >= 40:
        status = 'Average'
    else:
        status = 'Poor'

    return {
        'liquidity_score': round(liquidity_score, 1),
        'profitability_score': round(profitability_score, 1),
        'cash_flow_score': round(cash_flow_score, 1),
        'revenue_growth_score': round(revenue_growth_score, 1),
        'expense_control_score': round(expense_control_score, 1),
        'debt_ratio_score': round(debt_ratio_score, 1),
        'stability_score': stability_score,
        'status': status,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_profit': net_profit,
    }
