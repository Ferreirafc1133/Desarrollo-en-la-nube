import boto3
import uuid
import pdfkit
from rest_framework.response import Response
from rest_framework import status
from .serializers import NotaVentaSerializer, ContenidoNotaVentaSerializer
from django.conf import settings
from rest_framework.decorators import api_view


dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_notas = dynamodb.Table('NotasDeVenta')
table_contenido = dynamodb.Table('ContenidoNotasDeVenta')
s3 = boto3.client('s3', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')


@api_view(['POST'])
def crear_nota_venta_completa(request):
    cliente_id = request.data.get('cliente_id')
    productos = request.data.get('productos')
    direccion_facturacion_id = request.data.get('facturacion_id')
    direccion_envio_id = request.data.get('envio_id')
    return crear_nota_venta(cliente_id, productos, direccion_facturacion_id, direccion_envio_id)


def buscar_cliente(cliente_id):
    response = dynamodb.Table('Clientes').get_item(Key={'ID': cliente_id})
    cliente = response.get('Item', None)
    print(f"Resultado de buscar_cliente para cliente_id {cliente_id}: {cliente}")
    return cliente


def buscar_productos(productos_ids):
    productos = []
    for producto_id in productos_ids:
        response = dynamodb.Table('Productos').get_item(Key={'ID': producto_id})
        producto = response.get('Item', None)
        print(f"Resultado de buscar_productos para producto_id {producto_id}: {producto}")
        if producto:
            productos.append(producto)
    return productos


def buscar_domicilios(facturacion_id, envio_id):
    response_facturacion = dynamodb.Table('Domicilios').get_item(Key={'ID': facturacion_id})
    direccion_facturacion = response_facturacion.get('Item', None)
    print(f"Resultado de buscar_domicilios para facturacion_id {facturacion_id}: {direccion_facturacion}")

    response_envio = dynamodb.Table('Domicilios').get_item(Key={'ID': envio_id})
    direccion_envio = response_envio.get('Item', None)
    print(f"Resultado de buscar_domicilios para envio_id {envio_id}: {direccion_envio}")

    if direccion_facturacion and direccion_facturacion['tipo_direccion'] != 'FACTURACION':
        return {"error": "La dirección de facturación no es correcta"}
    
    if direccion_envio and direccion_envio['tipo_direccion'] != 'ENVIO':
        return {"error": "La dirección de envío no es correcta"}

    return {
        "DireccionFacturacion": direccion_facturacion,
        "DireccionEnvio": direccion_envio
    }


def generar_pdf(data):
    pdf_content = f"""
    <h1>Nota de Venta</h1>
    <p>Cliente: {data['Cliente']['nombre_comercial']}</p>
    <p>Dirección Facturación: {data['DireccionFacturacion']['domicilio']}</p>
    <p>Dirección Envío: {data['DireccionEnvio']['domicilio']}</p>
    <h2>Productos</h2>
    <ul>
    """
    for producto in data['Productos']:
        pdf_content += f"<li>{producto['nombre']} - {producto['Cantidad']} x ${producto['PrecioUnitario']} = ${producto['Importe']}</li>"
    pdf_content += f"</ul><p>Total: {data['Total']}</p>"

    pdf_file = pdfkit.from_string(pdf_content, False)
    return pdf_file


def subir_pdf_a_s3(pdf_file, bucket_name, file_name):
    try:
        s3.upload_fileobj(pdf_file, bucket_name, file_name)
        file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
        return file_url
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
        return None


def enviar_correo_cliente(email, mensaje, asunto):
    try:
        response = sns.publish(
            TopicArn='arn:aws:sns:us-east-1:583004271855:Practica3:d416f749-74ac-4331-9172-0a6923f9993d',
            Message=mensaje,
            Subject=asunto
        )
        return response
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return None


def crear_nota_venta(cliente_id, productos, direccion_facturacion_id, direccion_envio_id):
    cliente = buscar_cliente(cliente_id)
    if not cliente:
        print(f"Cliente con ID {cliente_id} no encontrado.")
        return Response({"error": "Cliente no encontrado"}, status=status.HTTP_400_BAD_REQUEST)
    
    domicilios = buscar_domicilios(direccion_facturacion_id, direccion_envio_id)
    if 'error' in domicilios:
        print(f"Error en domicilios: {domicilios['error']}")
        return Response({"error": domicilios['error']}, status=status.HTTP_400_BAD_REQUEST)

    nota_venta_id = str(uuid.uuid4())
    total = 0
    
    productos_info = buscar_productos([producto['ProductoID'] for producto in productos])
    if not productos_info:
        return Response({"error": "Productos no encontrados"}, status=status.HTTP_400_BAD_REQUEST)

    for producto, producto_info in zip(productos, productos_info):
        precio_unitario = producto_info['precio_base']
        importe = producto['Cantidad'] * precio_unitario
        total += importe

        contenido_nota_data = {
            "ID": str(uuid.uuid4()),
            "NotaID": nota_venta_id,
            "ProductoID": producto['ProductoID'],
            "Cantidad": producto['Cantidad'],
            "PrecioUnitario": precio_unitario,
            "Importe": importe
        }
        table_contenido.put_item(Item=contenido_nota_data)

    nota_venta_data = {
        "ID": nota_venta_id,
        "Cliente": cliente_id,
        "DireccionFacturacion": direccion_facturacion_id,
        "DireccionEnvio": direccion_envio_id,
        "Total": total
    }
    table_notas.put_item(Item=nota_venta_data)

    data_para_pdf = {
        "Cliente": cliente,
        "DireccionFacturacion": domicilios['DireccionFacturacion'],
        "DireccionEnvio": domicilios['DireccionEnvio'],
        "Productos": productos_info,
        "Total": total
    }

    pdf_file = generar_pdf(data_para_pdf)

    file_name = f"nota_venta_{nota_venta_id}.pdf"
    pdf_url = subir_pdf_a_s3(pdf_file, 'examenpract', file_name)

    if not pdf_url:
        print("Error al subir el PDF a S3")
        return Response({"error": "Error al subir el PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    mensaje = f"Se ha generado una nueva nota de venta. Puedes descargarla aqui: {pdf_url}"
    enviar_correo_cliente(cliente['correo_electronico'], mensaje, "Nota de Venta Generada")

    return Response({
        "mensaje": "Nota de venta creada correctamente",
        "nota_id": nota_venta_id,
        "pdf_url": pdf_url
    }, status=status.HTTP_201_CREATED)
