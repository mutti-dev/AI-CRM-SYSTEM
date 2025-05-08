from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Customer

@csrf_exempt
def fetch_customers(request):
    if request.method == 'GET':
        customers = Customer.objects.values('id', 'email', 'name', 'phone_number')
        return JsonResponse({
            'status': 'success', 
            'customers': list(customers)
        })
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def create_customer(request):
    if request.method == 'POST':
        try:
            data = request.json()
            customer = Customer.objects.create(
                email=data.get('email'),
                name=data.get('name'),
                phone_number=data.get('phone_number'),
                preferred_contact=data.get('preferred_contact', 'email')
            )
            return JsonResponse({
                'status': 'success',
                'customer': {
                    'id': customer.id,
                    'email': customer.email,
                    'name': customer.name,
                    'phone_number': customer.phone_number
                }
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
