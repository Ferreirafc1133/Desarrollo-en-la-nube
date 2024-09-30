import boto3
import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import DomicilioSerializer

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Domicilios')

@api_view(['GET'])
def domicilio_list(request):
    response = table.scan()
    domicilios = response.get('Items', [])

    return Response(domicilios, status=status.HTTP_200_OK)

@api_view(['POST'])
def domicilio_create(request):
    serializer = DomicilioSerializer(data=request.data)
    if serializer.is_valid():
        domicilio_data = serializer.validated_data

        if 'ID' not in domicilio_data:
            domicilio_data['ID'] = str(uuid.uuid4())

        table.put_item(Item=domicilio_data)

        return Response(domicilio_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def domicilio_detail(request, id):
    response = table.get_item(Key={'ID': id})
    domicilio = response.get('Item')

    if not domicilio:
        return Response({"message": "Domicilio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    return Response(domicilio, status=status.HTTP_200_OK)

@api_view(['PUT'])
def domicilio_update(request, id):
    response = table.get_item(Key={'ID': id})
    domicilio = response.get('Item')

    if not domicilio:
        return Response({"message": "Domicilio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    serializer = DomicilioSerializer(data=request.data, partial=True)
    if serializer.is_valid():
        domicilio_data = serializer.validated_data

        update_expression = "SET "
        expression_attribute_values = {}
        for key, value in domicilio_data.items():
            update_expression += f"{key} = :{key}, "
            expression_attribute_values[f":{key}"] = value

        update_expression = update_expression.rstrip(', ')

        table.update_item(
            Key={'ID': id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        return Response(domicilio_data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def domicilio_delete(request, id):
    response = table.get_item(Key={'ID': id})
    domicilio = response.get('Item')

    if not domicilio:
        return Response({"message": "Domicilio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    table.delete_item(Key={'ID': id})
    return Response({"message": "Domicilio eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
