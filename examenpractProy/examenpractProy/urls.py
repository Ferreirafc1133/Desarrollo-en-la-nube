from django.urls import path
from . import views_clientes

urlpatterns = [
    path('clientes/', views_clientes.cliente_list, name='cliente_list'),
    path('clientes/crear/', views_clientes.cliente_create, name='cliente_create'),
    path('clientes/<str:id>/', views_clientes.cliente_detail, name='cliente_detail'),
    path('clientes/<str:id>/editar/', views_clientes.cliente_update, name='cliente_update'),
    path('clientes/<str:id>/eliminar/', views_clientes.cliente_delete, name='cliente_delete'),
]
