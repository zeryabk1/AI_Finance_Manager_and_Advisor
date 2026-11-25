from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounting.views import get_active_company
from inventory.models import InventoryItem
from accounts.permissions import financial_write_required
from .models import Customer, Supplier, Budget, SalesInvoice, PurchaseBill, Payment
from .forms import (
    CustomerForm, SupplierForm, BudgetForm,
    SalesInvoiceForm, SalesInvoiceLineFormSet,
    PurchaseBillForm, PurchaseBillLineFormSet,
    PaymentForm,
)

def _limit_items_to_company(formset, company):
    """Only show this company's inventory items in the line-item dropdowns."""
    qs = InventoryItem.objects.filter(company=company)
    for line_form in formset.forms:
        line_form.fields['item'].queryset = qs
    formset.empty_form.fields['item'].queryset = qs
    return formset


# ---------------------------------------------------------------
# Customers
# ---------------------------------------------------------------

@login_required
def customer_list(request):
    company = get_active_company(request)
    customers = Customer.objects.filter(company=company) if company else Customer.objects.none()
    return render(request, 'transactions/customer_list.html', {'customers': customers, 'company': company})


@login_required
def customer_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            messages.success(request, 'Customer added.')
            return redirect('transactions:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Add Customer', 'back_url': 'transactions:customer_list'})


@login_required
def customer_update(request, pk):
    company = get_active_company(request)
    obj = get_object_or_404(Customer, pk=pk, company=company)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated.')
            return redirect('transactions:customer_list')
    else:
        form = CustomerForm(instance=obj)
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Edit Customer', 'back_url': 'transactions:customer_list'})


@login_required
def customer_delete(request, pk):
    company = get_active_company(request)
    obj = get_object_or_404(Customer, pk=pk, company=company)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Customer deleted.')
        return redirect('transactions:customer_list')
    return render(request, 'transactions/generic_confirm_delete.html', {'object': obj, 'back_url': 'transactions:customer_list'})


# ---------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------

@login_required
def supplier_list(request):
    company = get_active_company(request)
    suppliers = Supplier.objects.filter(company=company) if company else Supplier.objects.none()
    return render(request, 'transactions/supplier_list.html', {'suppliers': suppliers, 'company': company})


@login_required
def supplier_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            messages.success(request, 'Supplier added.')
            return redirect('transactions:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Add Supplier', 'back_url': 'transactions:supplier_list'})


@login_required
def supplier_update(request, pk):
    company = get_active_company(request)
    obj = get_object_or_404(Supplier, pk=pk, company=company)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated.')
            return redirect('transactions:supplier_list')
    else:
        form = SupplierForm(instance=obj)
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Edit Supplier', 'back_url': 'transactions:supplier_list'})


@login_required
def supplier_delete(request, pk):
    company = get_active_company(request)
    obj = get_object_or_404(Supplier, pk=pk, company=company)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Supplier deleted.')
        return redirect('transactions:supplier_list')
    return render(request, 'transactions/generic_confirm_delete.html', {'object': obj, 'back_url': 'transactions:supplier_list'})


# ---------------------------------------------------------------
# Budget
# ---------------------------------------------------------------

@login_required
def budget_list(request):
    company = get_active_company(request)
    budgets = Budget.objects.filter(company=company) if company else Budget.objects.none()
    return render(request, 'transactions/budget_list.html', {'budgets': budgets, 'company': company})


@login_required
@financial_write_required
def budget_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            messages.success(request, 'Budget added.')
            return redirect('transactions:budget_list')
    else:
        form = BudgetForm()
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Add Budget', 'back_url': 'transactions:budget_list'})


@login_required
@financial_write_required
def budget_update(request, pk):
    company = get_active_company(request)
    obj = get_object_or_404(Budget, pk=pk, company=company)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated.')
            return redirect('transactions:budget_list')
    else:
        form = BudgetForm(instance=obj)
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Edit Budget', 'back_url': 'transactions:budget_list'})


@login_required
@financial_write_required
def budget_delete(request, pk):
    company = get_active_company(request)
    obj = get_object_or_404(Budget, pk=pk, company=company)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Budget deleted.')
        return redirect('transactions:budget_list')
    return render(request, 'transactions/generic_confirm_delete.html', {'object': obj, 'back_url': 'transactions:budget_list'})


# ---------------------------------------------------------------
# Sales Invoices (with line items)
# ---------------------------------------------------------------

@login_required
def invoice_list(request):
    company = get_active_company(request)
    invoices = SalesInvoice.objects.filter(company=company) if company else SalesInvoice.objects.none()
    return render(request, 'transactions/invoice_list.html', {'invoices': invoices, 'company': company})


@login_required
def invoice_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = SalesInvoiceForm(request.POST, company=company)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.company = company
            invoice.save()
            formset = _limit_items_to_company(SalesInvoiceLineFormSet(request.POST, instance=invoice), company)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Invoice created.')
                return redirect('transactions:invoice_list')
            else:
                invoice.delete()
        else:
            formset = _limit_items_to_company(SalesInvoiceLineFormSet(request.POST), company)
    else:
        form = SalesInvoiceForm(company=company)
        formset = _limit_items_to_company(SalesInvoiceLineFormSet(), company)
    return render(request, 'transactions/invoice_form.html', {'form': form, 'formset': formset, 'title': 'New Sales Invoice'})


@login_required
def invoice_detail(request, pk):
    company = get_active_company(request)
    invoice = get_object_or_404(SalesInvoice, pk=pk, company=company)
    return render(request, 'transactions/invoice_detail.html', {'invoice': invoice})


# ---------------------------------------------------------------
# Purchase Bills (with line items)
# ---------------------------------------------------------------

@login_required
def bill_list(request):
    company = get_active_company(request)
    bills = PurchaseBill.objects.filter(company=company) if company else PurchaseBill.objects.none()
    return render(request, 'transactions/bill_list.html', {'bills': bills, 'company': company})


@login_required
def bill_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = PurchaseBillForm(request.POST, company=company)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.company = company
            bill.save()
            formset = _limit_items_to_company(PurchaseBillLineFormSet(request.POST, instance=bill), company)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Purchase bill created.')
                return redirect('transactions:bill_list')
            else:
                bill.delete()
        else:
            formset = _limit_items_to_company(PurchaseBillLineFormSet(request.POST), company)
    else:
        form = PurchaseBillForm(company=company)
        formset = _limit_items_to_company(PurchaseBillLineFormSet(), company)
    return render(request, 'transactions/bill_form.html', {'form': form, 'formset': formset, 'title': 'New Purchase Bill'})


@login_required
def bill_detail(request, pk):
    company = get_active_company(request)
    bill = get_object_or_404(PurchaseBill, pk=pk, company=company)
    return render(request, 'transactions/bill_detail.html', {'bill': bill})


# ---------------------------------------------------------------
# Payments
# ---------------------------------------------------------------

@login_required
def payment_list(request):
    company = get_active_company(request)
    payments = Payment.objects.filter(company=company) if company else Payment.objects.none()
    return render(request, 'transactions/payment_list.html', {'payments': payments, 'company': company})


@login_required
def payment_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = PaymentForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.save()
            messages.success(request, 'Payment recorded.')
            return redirect('transactions:payment_list')
    else:
        form = PaymentForm(company=company)
    return render(request, 'transactions/generic_form.html', {'form': form, 'title': 'Record Payment', 'back_url': 'transactions:payment_list'})
