"""
URL configuration for taskHorizon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tasks.views import list_tasks, create_task, update_task, delete_task  # Importa las vistas directamente


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', list_tasks, name='list_tasks'),
    path('create/', create_task, name='create_task'),
    path('update/<uuid:task_id>/', update_task, name='update_task'),
    path('delete/<uuid:task_id>/', delete_task, name='delete_task'),
]
