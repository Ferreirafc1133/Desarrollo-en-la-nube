from django.urls import path

urlpatterns = [
    # ruta final
    path('notas-venta/crear/', views_notas_ven.crear_nota_venta_completa, name='crear_nota_venta_completa'),
]

