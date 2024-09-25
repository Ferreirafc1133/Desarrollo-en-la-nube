from django.shortcuts import render, get_object_or_404, redirect
from .models import Task
from .forms import TaskForm

# Ver lista de tareas
def list_tasks(request):
    tasks = Task.objects.all()
    return render(request, 'task/list_task.html', {'tasks': tasks})

# Crear tarea
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
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
