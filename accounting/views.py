from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum

from companies.models import Company
from accounts.permissions import user_accessible_companies, financial_write_required
from .models import Account, JournalEntry
from .forms import AccountForm, JournalEntryForm


def get_active_company(request):
    """Returns the user's currently selected company (session-based), or the first one they can access."""
    accessible = user_accessible_companies(request.user)
    company_id = request.session.get('active_company_id')
    company = None
    if company_id:
        company = accessible.filter(pk=company_id).first()
    if not company:
        company = accessible.first()
        if company:
            request.session['active_company_id'] = company.pk
    return company


@login_required
def switch_company(request, pk):
    company = get_object_or_404(user_accessible_companies(request.user), pk=pk)
    request.session['active_company_id'] = company.pk
    messages.success(request, f'Switched to {company.name}.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:home'))


@login_required
def account_list(request):
    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()
    q = request.GET.get('q', '')
    account_type = request.GET.get('type', '')
    if q:
        accounts = accounts.filter(name__icontains=q)
    if account_type:
        accounts = accounts.filter(account_type=account_type)
    return render(request, 'accounting/account_list.html', {
        'accounts': accounts, 'company': company, 'q': q, 'account_type': account_type,
        'types': Account.AccountType.choices,
    })


@login_required
@financial_write_required
def account_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = AccountForm(request.POST, company=company)
        if form.is_valid():
            account = form.save(commit=False)
            account.company = company
            account.save()
            messages.success(request, 'Account added.')
            return redirect('accounting:account_list')
    else:
        form = AccountForm(company=company)
    return render(request, 'accounting/account_form.html', {'form': form, 'title': 'Add Account'})


@login_required
@financial_write_required
def account_update(request, pk):
    company = get_active_company(request)
    account = get_object_or_404(Account, pk=pk, company=company)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account updated.')
            return redirect('accounting:account_list')
    else:
        form = AccountForm(instance=account, company=company)
    return render(request, 'accounting/account_form.html', {'form': form, 'title': 'Edit Account'})


@login_required
@financial_write_required
def account_delete(request, pk):
    company = get_active_company(request)
    account = get_object_or_404(Account, pk=pk, company=company)
    if request.method == 'POST':
        account.delete()
        messages.success(request, 'Account deleted.')
        return redirect('accounting:account_list')
    return render(request, 'accounting/account_confirm_delete.html', {'account': account})


@login_required
def journal_list(request):
    company = get_active_company(request)
    entries = JournalEntry.objects.filter(company=company) if company else JournalEntry.objects.none()
    return render(request, 'accounting/journal_list.html', {'entries': entries, 'company': company})


@login_required
@financial_write_required
def journal_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, company=company)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.company = company
            entry.save()

            # AI fraud check: how often has this exact debit/credit account pair been used before?
            frequency = JournalEntry.objects.filter(
                company=company, debit_account=entry.debit_account, credit_account=entry.credit_account
            ).count()
            try:
                from ai_models.predict import score_journal_entry
                fraud_result = score_journal_entry(float(entry.amount), frequency)
                if fraud_result['is_anomaly']:
                    messages.warning(
                        request,
                        f"⚠️ AI Fraud Check: this entry scored a risk of {fraud_result['risk_score']}/100. "
                        f"{fraud_result['recommendation']}"
                    )
                else:
                    messages.success(request, f"Journal entry saved. AI fraud risk score: {fraud_result['risk_score']}/100 (normal).")
            except FileNotFoundError:
                messages.success(
                    request,
                    'Journal entry saved. (Run `python ai_models/train_fraud_model.py` once to enable AI fraud scoring.)'
                )
            return redirect('accounting:journal_list')
    else:
        form = JournalEntryForm(company=company)
    return render(request, 'accounting/journal_form.html', {'form': form, 'title': 'New Journal Entry'})


@login_required
def general_ledger(request):
    from .ledger import build_ledger
    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()
    ledger_data = []
    for account in accounts:
        data = build_ledger(account)
        ledger_data.append({
            'account': account,
            'entries': data['entries'],
            'closing': data['closing'],
            'normal_side': data['normal_side'],
        })
    return render(request, 'accounting/general_ledger.html', {'ledger_data': ledger_data, 'company': company})


@login_required
def trial_balance(request):
    company = get_active_company(request)
    accounts = Account.objects.filter(company=company) if company else Account.objects.none()
    rows = []
    total_debit = 0
    total_credit = 0
    for account in accounts:
        debit_total = account.debit_entries.aggregate(total=Sum('amount'))['total'] or 0
        credit_total = account.credit_entries.aggregate(total=Sum('amount'))['total'] or 0
        net = debit_total - credit_total
        debit_col = net if net > 0 else 0
        credit_col = -net if net < 0 else 0
        total_debit += debit_col
        total_credit += credit_col
        rows.append({'account': account, 'debit': debit_col, 'credit': credit_col})
    return render(request, 'accounting/trial_balance.html', {
        'rows': rows, 'total_debit': total_debit, 'total_credit': total_credit,
        'balanced': total_debit == total_credit, 'company': company,
    })


@login_required
def profit_and_loss(request):
    from .standards import build_income_statement
    company = get_active_company(request)
    return render(request, 'accounting/profit_and_loss.html', {
        'inc': build_income_statement(company), 'company': company,
    })


@login_required
def balance_sheet(request):
    from .standards import build_balance_sheet
    company = get_active_company(request)
    return render(request, 'accounting/balance_sheet.html', {
        'bs': build_balance_sheet(company), 'company': company,
    })
