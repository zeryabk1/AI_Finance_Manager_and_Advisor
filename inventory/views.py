from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounting.views import get_active_company
from datetime import date
from decimal import Decimal

from accounting.models import Account, JournalEntry
from .models import InventoryItem, StockLot
from .forms import InventoryItemForm, StockLotForm
from . import valuation


@login_required
def item_list(request):
    company = get_active_company(request)
    items = InventoryItem.objects.filter(company=company) if company else InventoryItem.objects.none()
    low_stock_count = sum(1 for i in items if i.is_low_stock)
    return render(request, 'inventory/item_list.html', {
        'items': items, 'company': company, 'low_stock_count': low_stock_count,
    })


@login_required
def item_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, company=company)
        if form.is_valid():
            item = form.save(commit=False)
            item.company = company
            item.save()
            if item.quantity > 0:   # opening stock layer so FIFO / LIFO / average have something to work with
                StockLot.objects.create(item=item, date=date.today(), quantity=item.quantity, unit_cost=item.cost_price)
            messages.success(request, 'Item added.')
            return redirect('inventory:item_list')
    else:
        form = InventoryItemForm(company=company)
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'Add Item'})


@login_required
def item_update(request, pk):
    company = get_active_company(request)
    item = get_object_or_404(InventoryItem, pk=pk, company=company)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated.')
            return redirect('inventory:item_list')
    else:
        form = InventoryItemForm(instance=item, company=company)
    return render(request, 'inventory/item_form.html', {'form': form, 'title': 'Edit Item'})


@login_required
def item_delete(request, pk):
    company = get_active_company(request)
    item = get_object_or_404(InventoryItem, pk=pk, company=company)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted.')
        return redirect('inventory:item_list')
    return render(request, 'inventory/item_confirm_delete.html', {'item': item})


@login_required
def lot_list(request, pk):
    company = get_active_company(request)
    item = get_object_or_404(InventoryItem, pk=pk, company=company)
    return render(request, 'inventory/lot_list.html', {'item': item, 'lots': item.lots.all(), 'company': company})


@login_required
def lot_create(request, pk):
    """Receive stock: add a purchase layer and increase on-hand quantity."""
    company = get_active_company(request)
    item = get_object_or_404(InventoryItem, pk=pk, company=company)
    if request.method == 'POST':
        form = StockLotForm(request.POST)
        if form.is_valid():
            lot = form.save(commit=False)
            lot.item = item
            lot.save()
            item.quantity += lot.quantity
            item.cost_price = lot.unit_cost          # latest purchase cost = current / replacement cost
            item.save(update_fields=['quantity', 'cost_price'])
            messages.success(request, f'Received {lot.quantity} unit(s) of {item.item_name} at {lot.unit_cost}.')
            return redirect('inventory:lot_list', pk=item.pk)
    else:
        form = StockLotForm(initial={'date': date.today(), 'unit_cost': item.cost_price})
    return render(request, 'inventory/item_form.html', {'form': form, 'title': f'Receive Stock - {item.item_name}'})


@login_required
def valuation_report(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    data = valuation.value_inventory(company)
    return render(request, 'inventory/valuation.html', {
        'company': company, 'data': data,
        'method_label': valuation.METHOD_LABELS[data['method']],
        'method_overridden': data['method'] != company.inventory_method,
        'ifrs': company.is_ifrs,
    })


def _inventory_account(company):
    acc = (Account.objects.filter(company=company, account_type=Account.AccountType.ASSET, name__icontains='inventory')
           .order_by('code').first())
    return acc or Account.objects.create(company=company, code='1200', name='Inventory', account_type=Account.AccountType.ASSET)


def _writedown_account(company):
    acc = Account.objects.filter(company=company, account_type=Account.AccountType.EXPENSE,
                                 name__iexact='Inventory Write-down').first()
    if acc:
        return acc
    code = 5450
    while Account.objects.filter(company=company, code=str(code)).exists():
        code += 1
    return Account.objects.create(company=company, code=str(code), name='Inventory Write-down',
                                  account_type=Account.AccountType.EXPENSE)


@login_required
def post_valuation(request):
    """Posts the write-down (or, under IFRS only, the reversal) to the ledger and records it per item."""
    if request.method != 'POST':
        return redirect('inventory:valuation')
    company = get_active_company(request)
    data = valuation.value_inventory(company)
    net = data['net_to_post']
    if net == 0:
        messages.info(request, 'Nothing to post - inventory is already carried at the correct amount.')
        return redirect('inventory:valuation')

    inv_acc, wd_acc = _inventory_account(company), _writedown_account(company)
    if net > 0:
        std = 'IAS 2' if company.is_ifrs else 'ASC 330'
        JournalEntry.objects.create(company=company, date=date.today(), amount=net, debit_account=wd_acc, credit_account=inv_acc,
                                    description=f'Inventory write-down to {"NRV" if company.is_ifrs else "lower of cost or NRV/market"} ({std})')
    else:  # only reachable under IFRS - US GAAP never produces a negative delta
        JournalEntry.objects.create(company=company, date=date.today(), amount=-net, debit_account=inv_acc, credit_account=wd_acc,
                                    description='Reversal of inventory write-down (IAS 2.33)')
    for r in data['rows']:
        if r['item'].recorded_writedown != r['new_recorded']:
            r['item'].recorded_writedown = r['new_recorded']
            r['item'].save(update_fields=['recorded_writedown'])
    messages.success(request, f'Posted inventory adjustment of {abs(net)} to the ledger.')
    return redirect('inventory:valuation')
