from django.urls import path

urlpatterns = [
    # prods
    path('productos/', views_prod.producto_list, name='producto_list'),
    path('productos/crear/', views_prod.producto_create, name='producto_create'),
    path('productos/<str:id>/', views_prod.producto_detail, name='producto_detail'),
    path('productos/<str:id>/editar/', views_prod.producto_update, name='producto_update'),
    path('productos/<str:id>/eliminar/', views_prod.producto_delete, name='producto_delete'),
    # clientes
    path('clientes/', views_clientes.cliente_list, name='cliente_list'),
    path('clientes/crear/', views_clientes.cliente_create, name='cliente_create'),
    path('clientes/<str:id>/', views_clientes.cliente_detail, name='cliente_detail'),
    path('clientes/<str:id>/editar/', views_clientes.cliente_update, name='cliente_update'),
    path('clientes/<str:id>/eliminar/', views_clientes.cliente_delete, name='cliente_delete'),
    # doms
    path('domicilios/', views_dom.domicilio_list, name='domicilio_list'),
    path('domicilios/crear/', views_dom.domicilio_create, name='domicilio_create'),
    path('domicilios/<str:id>/', views_dom.domicilio_detail, name='domicilio_detail'),
    path('domicilios/<str:id>/editar/', views_dom.domicilio_update, name='domicilio_update'),
    path('domicilios/<str:id>/eliminar/', views_dom.domicilio_delete, name='domicilio_delete'),
]

