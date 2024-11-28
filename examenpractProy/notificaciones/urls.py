from django.urls import path

urlpatterns = [
    # prods
    path('productos/', views_prod.producto_list, name='producto_list'),
    path('productos/crear/', views_prod.producto_create, name='producto_create'),
    path('productos/<str:id>/', views_prod.producto_detail, name='producto_detail'),
    path('productos/<str:id>/editar/', views_prod.producto_update, name='producto_update'),
    path('productos/<str:id>/eliminar/', views_prod.producto_delete, name='producto_delete'),
]

