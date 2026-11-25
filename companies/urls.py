from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='list'),
    path('add/', views.company_create, name='create'),
    path('<int:pk>/edit/', views.company_update, name='update'),
    path('<int:pk>/delete/', views.company_delete, name='delete'),
    path('<int:pk>/staff/', views.manage_staff, name='manage_staff'),
    path('<int:pk>/staff/<int:user_id>/remove/', views.remove_staff, name='remove_staff'),
]
