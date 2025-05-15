"""
URL configuration for _crm_system project.

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
import os
from django.contrib import admin
from django.urls import path, include, re_path
from frontend.views import FrontendAppView
from django.conf.urls.static import static
from django.conf import settings

# Customize admin site headers
admin.site.site_header = "MaxRemind CRM Admin"
admin.site.site_title = "MaxRemind CRM Portal"
admin.site.index_title = "Welcome to MaxRemind CRM Admin Panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^.*$', FrontendAppView.as_view()),
    path('api/emails/', include('email_handler.urls')),  # Email-related routes
    path('api/whatsapp/', include('whatsapp_handler.urls')),  # WhatsApp-related routes
    path('api/tasks/', include('tasks.urls')),  # Task-related routes
    path('api/customers/', include('customers.urls')),  # Customer-related routes
    path('api/users/', include('users.urls')),  # Agent and team-related routes
    path('api/ai/', include('ai_integration.urls')),  # AI-related routes
] + static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'web', 'build', 'static'))

