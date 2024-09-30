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
s3 = boto3.client('s3')
sns = boto3.client('sns')


@api_view(['POST'])
def crear_nota_venta_completa(request):
    # Recibir los datos del body de la solicitud
    cliente_id = request.data.get('cliente_id')
    productos = request.data.get('productos')
    direccion_facturacion_id = request.data.get('facturacion_id')
    direccion_envio_id = request.data.get('envio_id')

    # Llamar a la función para manejar la lógica de la creación de la nota de venta
    return crear_nota_venta(cliente_id, productos, direccion_facturacion_id, direccion_envio_id)

# buscar cliente
def buscar_cliente(cliente_id):
    response = dynamodb.Table('Clientes').get_item(Key={'ID': cliente_id})
    return response.get('Item', None)

# buscar producto
def buscar_productos(productos_ids):
    productos = []
    for producto_id in productos_ids:
        response = dynamodb.Table('Productos').get_item(Key={'ID': producto_id})
        producto = response.get('Item', None)
        if producto:
            productos.append(producto)
    
    if not productos:
        return {"error": "No se encontraron productos"}

    return productos

# buscar domicilio
def buscar_domicilios(facturacion_id, envio_id):
    response_facturacion = dynamodb.Table('Domicilios').get_item(Key={'ID': facturacion_id})
    direccion_facturacion = response_facturacion.get('Item', None)

    response_envio = dynamodb.Table('Domicilios').get_item(Key={'ID': envio_id})
    direccion_envio = response_envio.get('Item', None)

    if direccion_facturacion and direccion_facturacion['tipo_direccion'] != 'FACTURACIÓN':
        return {"error": "La dirección de facturación no es correcta"}
    
    if direccion_envio and direccion_envio['tipo_direccion'] != 'ENVÍO':
        return {"error": "La dirección de envío no es correcta"}

    return {
        "DireccionFacturacion": direccion_facturacion,
        "DireccionEnvio": direccion_envio
    }


# generar PDF
def generar_pdf(data):
    pdf_content = f"""
    <h1>Nota de Venta</h1>
    <p>Cliente: {data['Cliente']['nombre']}</p>
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

# subir a S3
def subir_pdf_a_s3(pdf_file, bucket_name, file_name):
    try:
        s3.upload_fileobj(pdf_file, bucket_name, file_name)
        file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
        return file_url
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
        return None

# enviar correo
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
    direccion_facturacion = buscar_domicilio(direccion_facturacion_id)
    direccion_envio = buscar_domicilio(direccion_envio_id)

    if not cliente or not direccion_facturacion or not direccion_envio:
        return Response({"error": "No se pudo encontrar la información necesaria"}, status=status.HTTP_400_BAD_REQUEST)

    nota_venta_id = str(uuid.uuid4())
    nota_venta_data = {
        "ID": nota_venta_id,
        "Cliente": cliente_id,
        "DireccionFacturacion": direccion_facturacion_id,
        "DireccionEnvio": direccion_envio_id,
        "Total": sum([producto['Cantidad'] * producto['PrecioUnitario'] for producto in productos])
    }
    table_notas.put_item(Item=nota_venta_data)

    for producto in productos:
        producto_info = buscar_producto(producto['ProductoID'])
        if not producto_info:
            continue

        contenido_nota_data = {
            "ID": str(uuid.uuid4()),
            "NotaID": nota_venta_id,
            "ProductoID": producto['ProductoID'],
            "Cantidad": producto['Cantidad'],
            "PrecioUnitario": producto['PrecioUnitario'],
            "Importe": producto['Cantidad'] * producto['PrecioUnitario']
        }
        table_contenido.put_item(Item=contenido_nota_data)

    data_para_pdf = {
        "Cliente": cliente,
        "DireccionFacturacion": direccion_facturacion,
        "DireccionEnvio": direccion_envio,
        "Productos": productos,
        "Total": nota_venta_data['Total']
    }

    # Generar PDF
    pdf_file = generar_pdf(data_para_pdf)

    # Subir a S3
    file_name = f"nota_venta_{nota_venta_id}.pdf"
    pdf_url = subir_pdf_a_s3(pdf_file, 'tu-bucket-de-s3', file_name)

    if not pdf_url:
        return Response({"error": "Error al subir el PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Enviar correo
    mensaje = f"Se ha generado una nueva nota de venta. Puedes descargarla aquí: {pdf_url}"
    enviar_correo_cliente(cliente['correo_electronico'], mensaje, "Nota de Venta Generada")

    return Response({
        "mensaje": "Nota de venta creada correctamente",
        "nota_id": nota_venta_id,
        "pdf_url": pdf_url
    }, status=status.HTTP_201_CREATED)
