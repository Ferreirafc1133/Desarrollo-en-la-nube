from django.urls import path
from examenpractApp import views_notas_ven  

urlpatterns = [
        path('notificaciones/enviar/', views_notas_ven.enviar_correo, name='enviar_correo'),

]

