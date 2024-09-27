from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, Archivo
from .forms import TaskForm
import boto3
from django.conf import settings


# Ver lista de tareas
def list_tasks(request):
    tasks = Task.objects.all()
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
                    Archivo.objects.create(tarea=task, url_archivo=file_url, tipo_archivo=archivo.content_type)
                except Exception as e:
                    print(f"Error subiendo archivo: {e}")
            
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
