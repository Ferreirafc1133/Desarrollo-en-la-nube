from rest_framework import serializers

class ClienteSerializer(serializers.Serializer):
    ID = serializers.CharField(max_length=100, required=False)
    razon_social = serializers.CharField(max_length=255)
    nombre_comercial = serializers.CharField(max_length=255)
    correo_electronico = serializers.EmailField()
