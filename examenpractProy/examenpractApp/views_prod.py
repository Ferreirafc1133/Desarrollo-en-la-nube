import boto3
import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductoSerializer

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Productos')

@api_view(['GET'])
def producto_list(request):
    response = table.scan()
    productos = response.get('Items', [])

    return Response(productos, status=status.HTTP_200_OK)

@api_view(['POST'])
def producto_create(request):
    serializer = ProductoSerializer(data=request.data)
    if serializer.is_valid():
        producto_data = serializer.validated_data

        if 'ID' not in producto_data:
            producto_data['ID'] = str(uuid.uuid4())

        table.put_item(Item=producto_data)

        return Response(producto_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def producto_detail(request, id):
    response = table.get_item(Key={'ID': id})
    producto = response.get('Item')

    if not producto:
        return Response({"message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    return Response(producto, status=status.HTTP_200_OK)

@api_view(['PUT'])
def producto_update(request, id):
    response = table.get_item(Key={'ID': id})
    producto = response.get('Item')

    if not producto:
        return Response({"message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductoSerializer(data=request.data, partial=True)
    if serializer.is_valid():
        producto_data = serializer.validated_data

        update_expression = "SET "
        expression_attribute_values = {}
        for key, value in producto_data.items():
            update_expression += f"{key} = :{key}, "
            expression_attribute_values[f":{key}"] = value

        update_expression = update_expression.rstrip(', ')

        table.update_item(
            Key={'ID': id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        return Response(producto_data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def producto_delete(request, id):
    response = table.get_item(Key={'ID': id})
    producto = response.get('Item')

    if not producto:
        return Response({"message": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    table.delete_item(Key={'ID': id})
    return Response({"message": "Producto eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
