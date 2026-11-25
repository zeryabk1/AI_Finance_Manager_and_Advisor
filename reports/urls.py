from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('trial-balance/pdf/', views.trial_balance_pdf, name='trial_balance_pdf'),
    path('trial-balance/excel/', views.trial_balance_excel, name='trial_balance_excel'),

    path('general-ledger/pdf/', views.general_ledger_pdf, name='general_ledger_pdf'),
    path('general-ledger/excel/', views.general_ledger_excel, name='general_ledger_excel'),

    path('profit-and-loss/pdf/', views.profit_loss_pdf, name='profit_loss_pdf'),
    path('profit-and-loss/excel/', views.profit_loss_excel, name='profit_loss_excel'),

    path('balance-sheet/pdf/', views.balance_sheet_pdf, name='balance_sheet_pdf'),
    path('balance-sheet/excel/', views.balance_sheet_excel, name='balance_sheet_excel'),

    path('fixed-assets/pdf/', views.fixed_assets_pdf, name='fixed_assets_pdf'),
    path('fixed-assets/excel/', views.fixed_assets_excel, name='fixed_assets_excel'),

    path('ai/', views.ai_dashboard, name='ai_dashboard'),
]
