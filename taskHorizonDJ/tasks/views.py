from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, Archivo
from .forms import TaskForm
import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.contrib import messages  
from django.http import JsonResponse, QueryDict
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import uuid 
from boto3.dynamodb.conditions import Attr
import json



dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
tasks_table = dynamodb.Table('Tareas')
files_table = dynamodb.Table('Archivos')

# Ver lista de tareas
def list_tasks(request):
    tasks_response = tasks_table.scan()
    tasks = tasks_response.get('Items', [])

    tasks_with_files = []

    for task in tasks:
        task_id = task['task_id']
        files_response = files_table.scan(
            FilterExpression=Attr('task_id').eq(task_id)
        )
        archivos = files_response.get('Items', [])
        tasks_with_files.append({
            'task': task,
            'archivos': archivos
        })

    return render(request, 'task/list_task.html', {'tasks_with_files': tasks_with_files})

# Crear tarea
@csrf_exempt
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            archivos = request.FILES.getlist('archivo')
            nombre_tarea = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            task_id = str(uuid.uuid4())
            fecha_subida = timezone.now().strftime('%Y%m%d_%H%M%S')

            tasks_table.put_item(
                Item={
                    'task_id': task_id,
                    'nombre_tarea': nombre_tarea,
                    'descripcion': descripcion,
                    'fecha_creacion': fecha_subida
                }
            )

            for archivo in archivos:
                if archivo.size <= 10 * 1024 * 1024:
                    s3 = boto3.client('s3')
                    bucket_name = 'tareasextra'
                    file_name = archivo.name
                    nombre_archivo = f"{file_name}_{fecha_subida}"
                    
                    try:
                        s3.upload_fileobj(
                            archivo,
                            bucket_name,
                            nombre_archivo,
                            ExtraArgs={
                                'Metadata': {
                                    'x-amz-meta-tarea': task_id,
                                    'x-amz-meta-cantidadDescargas': '0'
                                }
                            }
                        )
                        file_url = f"https://{bucket_name}.s3.amazonaws.com/{nombre_archivo}"
                        archivo_id = str(uuid.uuid4())

                        files_table.put_item(
                            Item={
                                'archivo_id': archivo_id,
                                'task_id': task_id,
                                'nombre_archivo': nombre_archivo,
                                'url_archivo': file_url,
                                'tipo_archivo': archivo.content_type,
                                'fecha_subida': fecha_subida,
                                'cantidad_descargas': 0
                            }
                        )

                    except Exception as e:
                        return JsonResponse({
                            "success": False,
                            "message": f"Error subiendo archivo a S3 o DynamoDB: {e}"
                        })
                else:
                    return JsonResponse({
                        "success": False,
                        "message": "Uno o más archivos exceden el límite de 10MB."
                    })

            return JsonResponse({
                "success": True,
                "message": "La tarea y los archivos se han creado correctamente.",
                "task_id": task_id
            })
        else:
            return JsonResponse({
                "success": False,
                "message": "Error al validar los datos del formulario.",
                "errors": form.errors
            })
    else:
        return JsonResponse({
            "success": False,
            "message": "Método no permitido. Usa POST."
        }, status=405)

# Actualizar tarea
@csrf_exempt
def update_task(request, task_id):
    if request.method == 'PUT':
        request.PUT = QueryDict(request.body)
        nombre_tarea = request.PUT.get('nombre')
        descripcion = request.PUT.get('descripcion')

        if nombre_tarea and descripcion:
            try:
                tasks_table.update_item(
                    Key={'task_id': task_id},
                    UpdateExpression="SET nombre_tarea = :n, descripcion = :d",
                    ExpressionAttributeValues={
                        ':n': nombre_tarea,
                        ':d': descripcion
                    }
                )

                # Notificar sobre la actualización
                send_sns_notification(nombre_tarea, "actualizada")

                return JsonResponse({
                    "success": True,
                    "message": "La tarea fue actualizada correctamente."
                })

            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": f"Error actualizando tarea en DynamoDB: {e}"
                })
        else:
            return JsonResponse({
                "success": False,
                "message": "Faltan campos en la solicitud."
            })

    return JsonResponse({
        "success": False,
        "message": "Método no permitido. Usa PUT."
    }, status=405)

# Eliminar tarea
@csrf_exempt
def delete_task(request, task_id):
    if request.method == 'DELETE':
        try:
            files_response = files_table.scan(
                FilterExpression=Attr('task_id').eq(task_id)
            )
            archivos = files_response.get('Items', [])

            if archivos:
                s3 = boto3.client('s3')
                for archivo in archivos:
                    try:
                        s3.delete_object(Bucket='tareasextra', Key=archivo['nombre_archivo'])
                        files_table.delete_item(Key={'archivo_id': archivo['archivo_id']})
                    except Exception as e:
                        return JsonResponse({
                            "success": False,
                            "message": f"Error eliminando archivo de S3: {e}"
                        })

            try:
                tasks_table.delete_item(Key={'task_id': task_id})
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": f"Error eliminando tarea de DynamoDB: {e}"
                })

            task_name = "nombre_tarea_eliminada"
            send_sns_notification(task_name, "eliminada")

            return JsonResponse({
                "success": True,
                "message": "La tarea y sus archivos fueron eliminados correctamente."
            })

        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error general durante la eliminación: {e}"
            })
    else:
        return JsonResponse({
            "success": False,
            "message": "Método no permitido. Usa DELETE."
        }, status=405)


def send_sns_notification(task_name, action):
    sns = boto3.client('sns', region_name='us-east-1')
    message = f"La tarea '{task_name}' ha sido {action}."
    try:
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:583004271855:Practica3:a50a0fe8-0ea0-4b50-81c8-f5a2da907d72',
            Message=message,
            PhoneNumber='+523320701024'
        )
    except Exception as e:
        print(f"Error enviando notificación SNS: {e}")
