from django.db import models

class Cliente(models.Model):
    razon_social = models.CharField(max_length=255)
    nombre_comercial = models.CharField(max_length=255)
    correo_electronico = models.EmailField(max_length=255, unique=True)

    def __str__(self):
        return self.razon_social
