from rest_framework import serializers

class ClienteSerializer(serializers.Serializer):
    ID = serializers.CharField(max_length=100, required=False)
    razon_social = serializers.CharField(max_length=255)
    nombre_comercial = serializers.CharField(max_length=255)
    correo_electronico = serializers.EmailField()

class DomicilioSerializer(serializers.Serializer):
    ID = serializers.CharField(max_length=100, required=False)
    domicilio = serializers.CharField(max_length=255)
    colonia = serializers.CharField(max_length=255)
    municipio = serializers.CharField(max_length=255)
    estado = serializers.CharField(max_length=255)
    tipo_direccion = serializers.ChoiceField(choices=['FACTURACIÓN', 'ENVÍO'])

class ProductoSerializer(serializers.Serializer):
    ID = serializers.CharField(max_length=100, required=False)
    nombre = serializers.CharField(max_length=255)
    unidad_medida = serializers.CharField(max_length=50)
    precio_base = serializers.DecimalField(max_digits=10, decimal_places=2)
