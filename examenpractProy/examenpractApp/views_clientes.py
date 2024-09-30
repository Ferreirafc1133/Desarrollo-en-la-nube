from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings  # Para acceder a la configuración de boto3
from .serializers import ClienteSerializer
import uuid

dynamodb = settings.dynamodb
table = dynamodb.Table('Clientes')

# Listar todos los clientes
@api_view(['GET'])
def cliente_list(request):
    response = table.scan()
    data = response.get('Items', [])
    return Response(data)

# Crear un nuevo cliente
@api_view(['POST'])
def cliente_create(request):
    serializer = ClienteSerializer(data=request.data)
    if serializer.is_valid():
        cliente_data = serializer.validated_data
        cliente_data['ID'] = str(uuid.uuid4())  # Generar un ID único
        table.put_item(Item=cliente_data)
        return Response(cliente_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Obtener un cliente por ID
@api_view(['GET'])
def cliente_detail(request, id):
    response = table.get_item(Key={'ID': id})
    cliente = response.get('Item')
    if cliente:
        return Response(cliente)
    return Response(status=status.HTTP_404_NOT_FOUND)

# Actualizar un cliente existente
@api_view(['PUT'])
def cliente_update(request, id):
    response = table.get_item(Key={'ID': id})
    cliente = response.get('Item')

    if not cliente:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ClienteSerializer(data=request.data)
    if serializer.is_valid():
        cliente_data = serializer.validated_data
        cliente_data['ID'] = id
        table.put_item(Item=cliente_data)  # Sobrescribir el cliente existente
        return Response(cliente_data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Eliminar un cliente
@api_view(['DELETE'])
def cliente_delete(request, id):
    response = table.get_item(Key={'ID': id})
    cliente = response.get('Item')

    if not cliente:
        return Response(status=status.HTTP_404_NOT_FOUND)

    table.delete_item(Key={'ID': id})
    return Response(status=status.HTTP_204_NO_CONTENT)
