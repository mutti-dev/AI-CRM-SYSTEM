from django.urls import path
from . import  views as customer_views

urlpatterns = [
    path('', customer_views.fetch_customers, name='fetch_customers'),
    path('create/', customer_views.create_customer, name='create_customer'),
]
