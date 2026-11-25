"""
accounts/permissions.py
-------------------------
Central place for role-based access rules, so every app checks
permissions the same way instead of re-inventing role logic.

Roles (accounts.models.User.Role):
    SUPER_ADMIN    - sees/manages every company in the system
    COMPANY_OWNER  - full control over the companies they own
    ACCOUNTANT     - full read/write on financial data for companies
                     they've been granted access to (cannot delete the
                     company or manage staff)
    EMPLOYEE       - read/write on day-to-day operational data
                     (customers, invoices, inventory), READ-ONLY on
                     financial data (chart of accounts, journal
                     entries, ledger, trial balance, budget)
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def is_super_admin(user):
    return user.is_authenticated and user.role == user.Role.SUPER_ADMIN


def is_company_owner(user):
    return user.is_authenticated and user.role == user.Role.COMPANY_OWNER


def is_accountant(user):
    return user.is_authenticated and user.role == user.Role.ACCOUNTANT


def is_employee(user):
    return user.is_authenticated and user.role == user.Role.EMPLOYEE


def can_manage_company(user, company=None):
    """Create/edit/delete a company, and manage its staff. Owner of that company or Super Admin only."""
    if is_super_admin(user):
        return True
    if company is not None:
        return company.owner_id == user.pk
    return is_company_owner(user)  # for the "create a new company" action, before a company exists


def can_write_financials(user):
    """Chart of Accounts, Journal Entries, Trial Balance edits, Budget. Employees get read-only."""
    return is_super_admin(user) or is_company_owner(user) or is_accountant(user)


def can_write_operations(user):
    """Customers, Suppliers, Sales/Purchase, Payments, Inventory, Fixed Assets. All roles can write."""
    return user.is_authenticated  # every logged-in role may operate day-to-day records


def user_accessible_companies(user):
    """Returns a queryset of companies this user is allowed to see."""
    from companies.models import Company
    if is_super_admin(user):
        return Company.objects.all()
    # .distinct() is required: Q(staff=user) joins the staff table, which otherwise returns the
    # same company once per staff member (looks like duplicate / "new" companies).
    return Company.objects.filter(models_q_owner_or_staff(user)).distinct()


def models_q_owner_or_staff(user):
    from django.db.models import Q
    return Q(owner=user) | Q(staff=user)


def financial_write_required(view_func):
    """Decorator: blocks Employees from create/update/delete views on financial data."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not can_write_financials(request.user):
            messages.error(request, "Your role (Employee) has read-only access to financial data. Ask your Company Owner or an Accountant to make this change.")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def company_manager_required(view_func):
    """Decorator: only the company's Owner or a Super Admin may proceed (used for company CRUD & staff management)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        pk = kwargs.get('pk')
        company = None
        if pk:
            from companies.models import Company
            company = Company.objects.filter(pk=pk).first()
        if not can_manage_company(request.user, company):
            messages.error(request, "Only the Company Owner or a Super Admin can do that.")
            return redirect('companies:list')
        return view_func(request, *args, **kwargs)
    return wrapper
