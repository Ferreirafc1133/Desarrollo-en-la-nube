from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, Archivo
from .forms import TaskForm
import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.contrib import messages  


# Ver lista de tareas
def list_tasks(request):
    tasks = Task.objects.prefetch_related('archivos').all()
    return render(request, 'task/list_task.html', {'tasks': tasks})

# Crear tarea
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save()  
            
            archivo = request.FILES.get('archivo')  
            if archivo:
                s3 = boto3.client('s3')
                bucket_name = 'tareasextra'
                file_name = archivo.name
                
                try:
                    s3.upload_fileobj(archivo, bucket_name, file_name)
                    
                    file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
                    
                    Archivo.objects.create(
                        tarea=task, 
                        url_archivo=file_url, 
                        tipo_archivo=archivo.content_type
                    )
                    
                    messages.success(request, "La tarea y el archivo se han creado correctamente.")
                    
                except FileNotFoundError:
                    print("El archivo no se encontró en el sistema local.")
                    messages.error(request, "El archivo no se encontró.")
                
                except NoCredentialsError:
                    print("Credenciales no disponibles.")
                    messages.error(request, "No se encontraron credenciales para subir el archivo a S3.")
                
                except PartialCredentialsError:
                    print("Credenciales incompletas.")
                    messages.error(request, "Las credenciales para S3 están incompletas.")
                
                except Exception as e:
                    print(f"Error subiendo archivo a S3: {e}")
                    messages.error(request, f"Error subiendo el archivo a S3: {e}")
            else:
                messages.warning(request, "La tarea se creó, pero no se subió ningún archivo.")
            
            return redirect('list_tasks')
    else:
        form = TaskForm()
    
    return render(request, 'task/create_task.html', {'form': form})


# Actualizar tarea
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
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.delete()
        return redirect('list_tasks')
    return render(request, 'task/detail_task.html', {'task': task})
