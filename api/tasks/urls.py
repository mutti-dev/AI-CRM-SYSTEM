from django.urls import path
from . import  views as task_views

urlpatterns = [
    path('assign-task/', task_views.assign_task, name='assign_task'),
    path('task-details/<int:email_query_id>/', task_views.fetch_task_details, name='fetch_task_details'),
    path('tasks-with-email-history/', task_views.fetch_tasks_with_email_history, name='fetch_tasks_with_email_history'),
]
