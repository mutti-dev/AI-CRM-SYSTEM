from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Agent, Team
import json
import logging

logger = logging.getLogger(__name__)




@csrf_exempt
def fetch_agents(request):
    if request.method == 'GET':
        agents = Agent.objects.values('id', 'user__first_name', 'user__last_name')
        agent_list = [
            {'id': agent['id'], 'name': f"{agent['user__first_name']} {agent['user__last_name']}"}
            for agent in agents
        ]
        return JsonResponse({'status': 'success', 'agents': agent_list})
    return JsonResponse({'error': 'Invalid request method'}, status=400)




@csrf_exempt
def fetch_teams(request):
    if request.method == 'GET':
        teams = Team.objects.values('id', 'name')
        return JsonResponse({'status': 'success', 'teams': list(teams)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

