"""
URL configuration for crm_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from email_handler import views

# Customize admin site headers
admin.site.site_header = "MaxRemind CRM Admin"
admin.site.site_title = "MaxRemind CRM Portal"
admin.site.index_title = "Welcome to MaxRemind CRM Admin Panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/fetch-emails/', views.fetch_unread_emails, name='fetch_emails'),
    path('api/process-queries/', views.process_queries, name='process_queries'),
    path('api/assign-task/', views.assign_task, name='assign_task'),
    path('api/reply-email/', views.reply_to_email, name='reply_email'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('api/customers/', views.fetch_customers, name='fetch_customers'),
    path('api/customers/create/', views.create_customer, name='create_customer'),
    path('api/unread-emails/', views.fetch_unread_emails_from_db, name='fetch_unread_emails_from_db'),
    path('api/email-details/<int:id>/', views.fetch_email_details, name='fetch_email_details'),
    path('api/email-replies/<int:id>/', views.fetch_email_replies, name='fetch_email_replies'),
    path('api/upload-dataset/', views.upload_fine_tuned_dataset, name='upload_fine_tuned_dataset'),
    path('api/agents/', views.fetch_agents, name='fetch_agents'),
    path('api/teams/', views.fetch_teams, name='fetch_teams'),
    path('api/task-details/<int:email_query_id>/', views.fetch_task_details, name='fetch_task_details'),
    path('api/tasks-with-email-history/', views.fetch_tasks_with_email_history, name='fetch_tasks_with_email_history'),
    path('api/tickets/<int:ticket_id>/', views.fetch_email_details, name='get_ticket'),
    
    # WhatsApp routes
    path('api/whatsapp/messages/', views.fetch_whatsapp_messages, name='fetch_whatsapp_messages'),
    path('api/whatsapp/details/<int:id>/', views.fetch_whatsapp_details, name='fetch_whatsapp_details'),
    path('api/whatsapp/reply/', views.reply_to_whatsapp, name='reply_to_whatsapp'),
    path('api/whatsapp/thread/<str:thread_id>/', views.fetch_whatsapp_thread, name='fetch_whatsapp_thread'),
    path('api/whatsapp/unread/', views.fetch_unread_whatsapp, name='fetch_unread_whatsapp'),
    path('api/whatsapp/test-connection/', views.test_whatsapp_connection, name='test_whatsapp_connection'),
]
