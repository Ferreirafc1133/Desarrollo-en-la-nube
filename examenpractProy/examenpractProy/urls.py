from django.urls import path, include 

urlpatterns = [
    path('catalogos/', include('catalogos.urls')),
    path('notas-venta/', include('notas_venta.urls')),
    path('notificaciones/', include('notificaciones.urls')),
]
