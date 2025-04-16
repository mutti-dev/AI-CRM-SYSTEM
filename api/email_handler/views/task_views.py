from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import Task, EmailQuery, Agent, Team, EmailReply
from django.utils.timezone import make_aware
from datetime import datetime
import json
import logging
import requests

logger = logging.getLogger(__name__)

@csrf_exempt
def assign_task(request):
    if request.method == 'POST':
        try:
            # Log the raw request body for debugging
            logging.debug("Raw request body: %s", request.body)

            data = json.loads(request.body)

            # Ensure 'email_query_id' exists in the request data
            if 'email_query_id' not in data:
                logging.error("'email_query_id' is missing in the request data.")
                return JsonResponse({'error': "'email_query_id' is required"}, status=400)

            # Parse and make the due_date timezone-aware
            due_date = None
            if data.get('due_date'):
                try:
                    naive_due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
                    due_date = make_aware(naive_due_date)  # Convert to timezone-aware datetime
                except ValueError as e:
                    logging.error(f"Invalid due_date format: {e}")
                    return JsonResponse({'error': 'Invalid due_date format'}, status=400)

            email_query = EmailQuery.objects.get(id=data['email_query_id'])
            task = Task.objects.create(
                email_query=email_query,
                title=data['title'],
                description=data['description'],
                assigned_team_id=data.get('assigned_team_id'),
                assigned_agent_id=data.get('assigned_agent_id'),
                due_date=due_date
            )

            # Send task details to Microsoft Teams using a webhook
            try:
                # webhook_url = WEBHOOK_URL
                webhook_url = "https://pern.webhook.office.com/webhookb2/b6bdde7c-c22b-46b5-bf7a-d4a02cc0daf8@75df096c-8b72-48e4-9b91-cbf79d87ee3a/IncomingWebhook/f8eb4c6e70e4455f93aa38aee66192c0/c8dba7ff-6bfd-4f06-92f2-fa8f96b5e923/V2bpRDyrGmWZHn2QJfTpZWjPY-pcpdqXKPAYOU1Mn3ED81"
                assigned_agent = Agent.objects.get(id=data.get('assigned_agent_id')).user.get_full_name() if data.get('assigned_agent_id') else "N/A"
                assigned_team = Team.objects.get(id=data.get('assigned_team_id')).name if data.get('assigned_team_id') else "N/A"

                # Handle None for due_date
                due_date_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A"

                message = {
                    "title": "New Task Assigned",
                    "text": f"A new task has been assigned to **{assigned_agent if assigned_agent != 'N/A' else assigned_team}**.",
                    "sections": [
                        {
                            "activityTitle": f"**Task Title:** {task.title}",
                            "activitySubtitle": f"**Description:** {task.description}",
                            "facts": [
                                {"name": "Assigned Agent:", "value": assigned_agent},
                                {"name": "Assigned Team:", "value": assigned_team},
                                {"name": "Due Date:", "value": due_date_str},
                                {"name": "Email Query Subject:", "value": email_query.subject},
                            ],
                            "markdown": True
                        }
                    ],
                    "potentialAction": [
                        {
                            "@type": "OpenUri",
                            "name": "View Task",
                            "targets": [
                                {"os": "default", "uri": f"http://localhost:3000/details/{task.id}"}
                            ]
                        }
                    ]
                }

                logging.debug(f"Webhook URL: {webhook_url}")
                logging.debug(f"Payload: {message}")
                response = requests.post(webhook_url, json=message)
                if response.status_code != 200:
                    logging.error(f"Failed to send message to Teams: {response.status_code}, {response.text}")
            except Exception as e:
                logging.error(f"Error sending task details to Teams: {e}")

            return JsonResponse({'status': 'success', 'task_id': task.id})
        except EmailQuery.DoesNotExist:
            logging.error("EmailQuery not found for the provided 'email_query_id'.")
            return JsonResponse({'error': 'EmailQuery not found'}, status=404)
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON in request body: %s", e)
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logging.error(f"Error in assign_task: {e}")
            return JsonResponse({'error': 'An error occurred while assigning the task'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_task_details(request, email_query_id):
    if request.method == 'GET':
        try:
            task = Task.objects.filter(email_query_id=email_query_id).first()
            if task:
                task_data = {
                    'title': task.title,
                    'description': task.description,
                    'assigned_agent_id': task.assigned_agent.id if task.assigned_agent else None,
                    'assigned_team_id': task.assigned_team.id if task.assigned_team else None,
                    'due_date': task.due_date,
                }
                return JsonResponse({'status': 'success', 'task': task_data})
            else:
                return JsonResponse({'status': 'success', 'task': None})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_tasks_with_email_history(request):
    if request.method == 'GET':
        try:
            tasks = Task.objects.select_related('email_query', 'assigned_agent', 'assigned_team').all()
            task_list = []
            for task in tasks:
                email_query = task.email_query
                email_history = EmailReply.objects.filter(email_query=email_query).values(
                    'id', 'content', 'sent_at', 'responder__user__first_name', 'responder__user__last_name'
                )
                task_list.append({
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'status': task.status,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'assigned_agent': task.assigned_agent.user.get_full_name() if task.assigned_agent else None,
                    'assigned_team': task.assigned_team.name if task.assigned_team else None,
                    'email_query': {
                        'id': email_query.id,
                        'subject': email_query.subject,
                        'content': email_query.content,
                        'received_at': email_query.received_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'customer_email': email_query.customer.email,
                    },
                    'email_history': list(email_history),
                })
            return JsonResponse({'status': 'success', 'tasks': task_list})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)