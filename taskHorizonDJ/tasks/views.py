from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, Archivo
from .forms import TaskForm
import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.contrib import messages  
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Ver lista de tareas
@csrf_exempt
def list_tasks(request):
    tasks = Task.objects.prefetch_related('archivos').all()
    return render(request, 'task/list_task.html', {'tasks': tasks})

# Crear tarea
@csrf_exempt
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES.get('archivo')
            if archivo:
                s3 = boto3.client('s3')
                bucket_name = 'tareasextra'
                file_name = archivo.name

                try:
                    s3.upload_fileobj(archivo, bucket_name, file_name)

                    file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"

                    task = form.save()

                    Archivo.objects.create(
                        tarea=task,
                        url_archivo=file_url,
                        tipo_archivo=archivo.content_type
                    )

                    return JsonResponse({
                        "success": True,
                        "message": "La tarea y el archivo se han creado correctamente.",
                        "file_url": file_url,
                        "task_id": task.id
                    })

                except FileNotFoundError:
                    return JsonResponse({
                        "success": False,
                        "message": "El archivo no se encontró en el sistema local."
                    })

                except NoCredentialsError:
                    return JsonResponse({
                        "success": False,
                        "message": "No se encontraron credenciales para subir el archivo a S3."
                    })

                except PartialCredentialsError:
                    return JsonResponse({
                        "success": False,
                        "message": "Las credenciales para S3 están incompletas."
                    })

                except Exception as e:
                    return JsonResponse({
                        "success": False,
                        "message": f"Error subiendo archivo a S3: {e}"
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
