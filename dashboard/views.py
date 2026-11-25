from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

from accounts.permissions import user_accessible_companies
from accounting.models import Account, JournalEntry
from accounting.views import get_active_company


@login_required
def home(request):
    companies = user_accessible_companies(request.user)
    company = get_active_company(request)

    revenue = expenses = 0
    recent_entries = []
    if company:
        revenue_accounts = Account.objects.filter(company=company, account_type=Account.AccountType.REVENUE)
        expense_accounts = Account.objects.filter(company=company, account_type=Account.AccountType.EXPENSE)
        revenue = sum(a.balance for a in revenue_accounts) * -1  # revenue grows on credit side
        expenses = sum(a.balance for a in expense_accounts)
        recent_entries = JournalEntry.objects.filter(company=company).order_by('-date', '-created_at')[:8]

    context = {
        'companies': companies,
        'company': company,
        'companies_count': companies.count(),
        'revenue': revenue,
        'expenses': expenses,
        'profit': revenue - expenses,
        'recent_entries': recent_entries,
    }
    return render(request, 'dashboard/home.html', context)
