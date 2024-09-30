from django.urls import path
from . import views_clientes

urlpatterns = [
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/crear/', views.cliente_create, name='cliente_create'),
    path('clientes/<str:id>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<str:id>/editar/', views.cliente_update, name='cliente_update'),
    path('clientes/<str:id>/eliminar/', views.cliente_delete, name='cliente_delete'),
]
