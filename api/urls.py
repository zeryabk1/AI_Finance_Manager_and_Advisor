from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('companies', views.CompanyViewSet, basename='api-companies')
router.register('accounts', views.AccountViewSet, basename='api-accounts')
router.register('journal-entries', views.JournalEntryViewSet, basename='api-journal-entries')
router.register('inventory', views.InventoryItemViewSet, basename='api-inventory')
router.register('customers', views.CustomerViewSet, basename='api-customers')
router.register('suppliers', views.SupplierViewSet, basename='api-suppliers')

urlpatterns = [
    path('register/', views.api_register, name='api_register'),
    path('login/', views.ApiLoginView.as_view(), name='api_login'),
    path('', include(router.urls)),
]
