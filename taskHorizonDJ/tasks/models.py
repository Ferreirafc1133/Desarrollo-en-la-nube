from django.db import models
from django.utils import timezone
from datetime import timedelta

class Task(models.Model):
    nombre = models.CharField(max_length=255)
    fecha = models.DateTimeField(default=timezone.now)
    descripcion = models.TextField()
    
    def __str__(self):
        return self.nombre

    def is_expired(self):
        return timezone.now() > self.fecha + timedelta(days=30)

class Archivo(models.Model):
    tarea = models.ForeignKey(Task, related_name='archivos', on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='tareas/')
    tipo_archivo = models.CharField(max_length=50)
    cantidad_descargas = models.IntegerField(default=0)

    def __str__(self):
        return f"Archivo de {self.tarea.nombre}"
