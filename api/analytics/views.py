from django.http import JsonResponse
from email_handler.models import EmailQuery, Task, EmailLog

def dashboard_data(request):
    if request.method == 'GET':
        data = {
            'queries': EmailQuery.objects.all().count(),
            'replied_queries': EmailQuery.objects.filter(is_replied=True).count(),
            'complex_queries': EmailQuery.objects.filter(is_complex=True).count(),
            'tasks': Task.objects.all().count(),
            'logs': EmailLog.objects.all().count()
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

