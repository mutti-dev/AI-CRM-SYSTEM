from django.contrib import admin
from django.template.response import TemplateResponse

class CustomAdminSite(admin.AdminSite):
    site_header = "MaxRemind CRM Admin"
    site_title = "MaxRemind CRM Portal"
    index_title = "Welcome to MaxRemind CRM Admin Panel"

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = '/static/admin/css/custom_admin.css'  # Corrected path
        context['company_logo'] = '/static/admin/img/company_logo.png'  # Path to the company logo
        return context

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['company_logo'] = '/static/admin/img/company_logo.png'  # Path to the company logo
        return super().index(request, extra_context)

admin_site = CustomAdminSite(name='custom_admin')
