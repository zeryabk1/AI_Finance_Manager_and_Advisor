"""
cash_flow_prediction.py
-------------------------
Predicts next month's income, expenses, and net cash flow.

Approach: aggregate the company's real JournalEntry data into monthly
income (revenue-account credits) and expense (expense-account debits)
totals, then fit a simple linear regression (scikit-learn) on the
monthly time series to project one month ahead. If there isn't enough
real history yet (fewer than 3 months of data), falls back to a flat
projection based on the average of whatever data exists so the page
still renders something meaningful for a brand-new company.

Usage:
    from ai_models.cash_flow_prediction import predict_next_month_cash_flow
    result = predict_next_month_cash_flow(company)
"""
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LinearRegression

from accounting.models import Account, JournalEntry


def _monthly_totals(company):
    entries = JournalEntry.objects.filter(company=company).select_related('debit_account', 'credit_account')

    income_by_month = defaultdict(float)
    expense_by_month = defaultdict(float)

    for e in entries:
        key = (e.date.year, e.date.month)
        if e.credit_account.account_type == Account.AccountType.REVENUE:
            income_by_month[key] += float(e.amount)
        if e.debit_account.account_type == Account.AccountType.EXPENSE:
            expense_by_month[key] += float(e.amount)

    months = sorted(set(income_by_month) | set(expense_by_month))
    income_series = [income_by_month[m] for m in months]
    expense_series = [expense_by_month[m] for m in months]
    return months, income_series, expense_series


def _project_next(series):
    """Fit a simple linear trend and project one step ahead; fall back to average if too little data."""
    n = len(series)
    if n == 0:
        return 0.0
    if n < 3:
        return round(sum(series) / n, 2)

    X = np.arange(n).reshape(-1, 1)
    y = np.array(series)
    model = LinearRegression()
    model.fit(X, y)
    next_value = model.predict([[n]])[0]
    return round(max(0.0, float(next_value)), 2)


def predict_next_month_cash_flow(company):
    months, income_series, expense_series = _monthly_totals(company)

    predicted_income = _project_next(income_series)
    predicted_expenses = _project_next(expense_series)
    net_cash_flow = round(predicted_income - predicted_expenses, 2)

    history = [
        {
            'label': f"{y}-{m:02d}",
            'income': income_series[i],
            'expenses': expense_series[i],
        }
        for i, (y, m) in enumerate(months)
    ]

    return {
        'history': history,
        'predicted_income': predicted_income,
        'predicted_expenses': predicted_expenses,
        'net_cash_flow': net_cash_flow,
        'has_enough_data': len(months) >= 3,
    }
