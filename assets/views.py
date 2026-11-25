from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from accounting.views import get_active_company
from .models import FixedAsset
from .forms import FixedAssetForm


@login_required
def asset_list(request):
    company = get_active_company(request)
    assets = FixedAsset.objects.filter(company=company) if company else FixedAsset.objects.none()
    total_book_value = sum(a.current_book_value for a in assets)
    return render(request, 'assets/asset_list.html', {'assets': assets, 'company': company, 'total_book_value': total_book_value})


@login_required
def asset_create(request):
    company = get_active_company(request)
    if not company:
        messages.warning(request, 'Please create a company first.')
        return redirect('companies:create')
    if request.method == 'POST':
        form = FixedAssetForm(request.POST, company=company)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.company = company
            asset.save()
            messages.success(request, 'Asset added.')
            return redirect('assets:asset_list')
    else:
        form = FixedAssetForm(company=company)
    return render(request, 'assets/asset_form.html', {'form': form, 'title': 'Add Fixed Asset'})


@login_required
def asset_update(request, pk):
    company = get_active_company(request)
    asset = get_object_or_404(FixedAsset, pk=pk, company=company)
    if request.method == 'POST':
        form = FixedAssetForm(request.POST, instance=asset, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset updated.')
            return redirect('assets:asset_list')
    else:
        form = FixedAssetForm(instance=asset, company=company)
    return render(request, 'assets/asset_form.html', {'form': form, 'title': 'Edit Fixed Asset'})


@login_required
def asset_delete(request, pk):
    company = get_active_company(request)
    asset = get_object_or_404(FixedAsset, pk=pk, company=company)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted.')
        return redirect('assets:asset_list')
    return render(request, 'assets/asset_confirm_delete.html', {'asset': asset})
