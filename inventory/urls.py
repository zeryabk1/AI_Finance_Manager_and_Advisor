from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('add/', views.item_create, name='item_create'),
    path('<int:pk>/edit/', views.item_update, name='item_update'),
    path('valuation/', views.valuation_report, name='valuation'),
    path('valuation/post/', views.post_valuation, name='post_valuation'),
    path('<int:pk>/lots/', views.lot_list, name='lot_list'),
    path('<int:pk>/receive/', views.lot_create, name='lot_create'),
    path('<int:pk>/delete/', views.item_delete, name='item_delete'),
]
