from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FineTunedDataset
import json
import logging

logger = logging.getLogger(__name__)






@csrf_exempt
def upload_fine_tuned_dataset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dataset = FineTunedDataset.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                data=data['data']
            )
            return JsonResponse({
                'status': 'success', 
                'dataset_id': dataset.id
            })
        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
