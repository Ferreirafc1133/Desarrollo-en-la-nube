from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, Archivo
from .forms import TaskForm
import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.contrib import messages  
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import uuid 


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
        files_response = files_table.query(
            IndexName='task_idIndex',
            KeyConditionExpression=Key('task_id').eq(task_id)
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
            archivo = request.FILES.get('archivo')
            nombre_tarea = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            if archivo:
                s3 = boto3.client('s3')
                bucket_name = 'tareasextra'
                file_name = archivo.name
                fecha_subida = timezone.now().strftime('%Y%m%d_%H%M%S')
                nombre_archivo = f"{file_name}_{fecha_subida}"

                try:
                    s3.upload_fileobj(archivo, bucket_name, nombre_archivo)
                    file_url = f"https://{bucket_name}.s3.amazonaws.com/{nombre_archivo}"

                    task_id = str(uuid.uuid4())
                    archivo_id = str(uuid.uuid4())

                    tasks_table.put_item(
                        Item={
                            'task_id': task_id,
                            'nombre_tarea': nombre_tarea,
                            'descripcion': descripcion,
                            'fecha_creacion': fecha_subida
                        }
                    )

                    files_table.put_item(
                        Item={
                            'archivo_id': archivo_id,
                            'task_id': task_id,
                            'nombre_archivo': nombre_archivo,
                            'url_archivo': file_url,
                            'tipo_archivo': archivo.content_type,
                            'fecha_subida': fecha_subida
                        }
                    )

                    return JsonResponse({
                        "success": True,
                        "message": "La tarea y el archivo se han creado correctamente.",
                        "file_url": file_url,
                        "task_id": task_id,
                        "archivo_id": archivo_id
                    })

                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "message": f"Error subiendo archivo a S3 o DynamoDB: {e}"
                    })
            else:
                return JsonResponse({
                    "success": False,
                    "message": "No se recibió ningún archivo para subir."
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
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('list_tasks')
    else:
        form = TaskForm(instance=task)
    return render(request, 'task/update_task.html', {'form': form, 'task': task})

# Eliminar tarea
@csrf_exempt
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.delete()
        return redirect('list_tasks')
    return render(request, 'task/detail_task.html', {'task': task})
