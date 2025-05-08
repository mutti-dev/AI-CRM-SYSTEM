from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'preferred_contact', 'created_at')
    search_fields = ('name', 'email', 'phone_number')
    list_filter = ('preferred_contact', 'created_at')





