from django.urls import path
from examenpractApp  import views_notas_ven

urlpatterns = [
    # ruta final
    path('crear/', views_notas_ven.crear_nota_venta_completa, name='crear_nota_venta_completa'),
]

