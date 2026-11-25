from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/add/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_update, name='account_update'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),

    path('journal/', views.journal_list, name='journal_list'),
    path('journal/add/', views.journal_create, name='journal_create'),

    path('ledger/', views.general_ledger, name='ledger'),
    path('trial-balance/', views.trial_balance, name='trial_balance'),
    path('profit-and-loss/', views.profit_and_loss, name='profit_and_loss'),
    path('balance-sheet/', views.balance_sheet, name='balance_sheet'),

    path('switch-company/<int:pk>/', views.switch_company, name='switch_company'),
]
