from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model

from accounts.permissions import (
    is_super_admin, can_manage_company, company_manager_required, user_accessible_companies,
)
from .models import Company
from .forms import CompanyForm, CreateStaffForm

User = get_user_model()


@login_required
def company_list(request):
    query = request.GET.get('q', '')
    companies = user_accessible_companies(request.user)
    if query:
        companies = companies.filter(name__icontains=query)
    return render(request, 'companies/company_list.html', {
        'companies': companies, 'query': query, 'is_super_admin': is_super_admin(request.user),
    })


@login_required
def company_create(request):
    if not can_manage_company(request.user):
        messages.error(request, "Only a Company Owner or Super Admin can create a company. Ask your Company Owner to grant you access to an existing one instead.")
        return redirect('companies:list')
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            messages.success(request, 'Company created successfully.')
            return redirect('companies:list')
    else:
        form = CompanyForm()
    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Add Company'})


@login_required
@company_manager_required
def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully.')
            return redirect('companies:list')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'companies/company_form.html', {'form': form, 'title': 'Edit Company'})


@login_required
@company_manager_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        messages.success(request, 'Company deleted.')
        return redirect('companies:list')
    return render(request, 'companies/company_confirm_delete.html', {'company': company})


@login_required
@company_manager_required
def manage_staff(request, pk):
    """
    Company Owner creates an Accountant/Employee login (email + password
    + role) in one step, and that account is immediately granted access
    to THIS company. If the email already belongs to an existing
    Accountant/Employee account, access is simply granted to it instead
    (no duplicate account, password/role are left as they already are).
    """
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CreateStaffForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']

            user = User.objects.filter(email__iexact=email).first()
            if user:
                company.staff.add(user)
                messages.success(request, f'{user.email} already had an account — granted {user.get_role_display()} access to {company.name}.')
            else:
                first_name, _, last_name = full_name.partition(' ')
                username = email
                if User.objects.filter(username__iexact=username).exists():
                    # extremely rare: someone else's username happens to equal this email
                    username = f"{email}.{company.pk}"
                user = User.objects.create_user(
                    username=username, email=email, password=password,
                    role=role, first_name=first_name, last_name=last_name,
                )
                company.staff.add(user)
                messages.success(
                    request,
                    f'Account created for {email} as {user.get_role_display()}. '
                    f'Share these login details with them: email "{email}" and the password you just set. '
                    f'They can log in at the same login page using their email.'
                )
            return redirect('companies:manage_staff', pk=company.pk)
    else:
        form = CreateStaffForm()
    return render(request, 'companies/manage_staff.html', {'company': company, 'form': form})


@login_required
@company_manager_required
def remove_staff(request, pk, user_id):
    company = get_object_or_404(Company, pk=pk)
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        company.staff.remove(user)
        messages.success(request, f'{user.email} no longer has access to {company.name}.')
    return redirect('companies:manage_staff', pk=company.pk)
