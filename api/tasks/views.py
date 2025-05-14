import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Task
from whatsapp_handler.models import WhatsAppMessage, WhatsAppReply
from users.models import Agent, Team
from email_handler.models import EmailQuery, EmailReply
from django.utils.timezone import make_aware
from datetime import datetime
import json
import logging
import requests
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)



@csrf_exempt
def assign_task(request):
    if request.method == 'POST':
        try:
            # Log the raw request body for debugging
            logging.debug("Raw request body: %s", request.body)

            data = json.loads(request.body)
            print("whatsapp query", data)

            # Ensure at least one of 'email_query_id' or 'whatsapp_query_id' exists in the request data
            if not data.get('email_query_id') and not data.get('whatsapp_query_id'):
                logging.error("'email_query_id' or 'whatsapp_query_id' is missing in the request data.")
                return JsonResponse({'error': "'email_query_id' or 'whatsapp_query_id' is required"}, status=400)

            # Parse and make the due_date timezone-aware
            due_date = None
            if data.get('due_date'):
                try:
                    naive_due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
                    due_date = make_aware(naive_due_date)  # Convert to timezone-aware datetime
                except ValueError as e:
                    logging.error(f"Invalid due_date format: {e}")
                    return JsonResponse({'error': 'Invalid due_date format'}, status=400)

            # Fetch the email_query or whatsapp_query based on the provided ID
            email_query = None
            whatsapp_query = None

            if data.get('email_query_id'):
                try:
                    email_query = EmailQuery.objects.get(id=data['email_query_id'])
                except EmailQuery.DoesNotExist:
                    logging.error("EmailQuery not found.")
                    return JsonResponse({'error': 'EmailQuery not found'}, status=404)

            if data.get('whatsapp_query_id'):
                try:
                    whatsapp_query = WhatsAppMessage.objects.get(whatsapp_message_id=data['whatsapp_query_id'])
                except WhatsAppMessage.DoesNotExist:
                    logging.error("WhatsAppMessage not found.")
                    return JsonResponse({'error': 'WhatsAppMessage not found'}, status=404)

            # Fetch the assigned agent and team
            assigned_agent = None
            assigned_team = None

            if data.get('assigned_agent_id'):
                try:
                    assigned_agent = Agent.objects.get(id=data['assigned_agent_id'])
                except Agent.DoesNotExist:
                    logging.warning("Assigned agent not found. ID: %s", data.get('assigned_agent_id'))

            if data.get('assigned_team_id'):
                try:
                    assigned_team = Team.objects.get(id=data.get('assigned_team_id'))
                except Team.DoesNotExist:
                    logging.warning("Assigned team not found. ID: %s", data.get('assigned_team_id'))

            # Create the task
            task = Task.objects.create(
                email_query=email_query,
                whatsapp_query=whatsapp_query,
                title=data['title'],
                description=data['description'],
                assigned_team=assigned_team,
                assigned_agent=assigned_agent,
                due_date=due_date
            )

            # Send task details to Microsoft Teams using a webhook
            try:
                webhook_url = os.getenv('TEAMS_WEBHOOK_URL')

                # Handle None for due_date
                due_date_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A"

                message = {
                    "title": "New Task Assigned",
                    "text": f"A new task has been assigned to **{assigned_agent.user.get_full_name() if assigned_agent else assigned_team.name if assigned_team else 'N/A'}**.",
                    "sections": [
                        {
                            "activityTitle": f"**Task Title:** {task.title}",
                            "activitySubtitle": f"**Description:** {task.description}",
                            "facts": [
                                {"name": "Assigned Agent:", "value": assigned_agent.user.get_full_name() if assigned_agent else "N/A"},
                                {"name": "Assigned Team:", "value": assigned_team.name if assigned_team else "N/A"},
                                {"name": "Due Date:", "value": due_date_str},
                                {"name": "Email Query Subject:", "value": email_query.subject if email_query else "N/A"},
                                {"name": "WhatsApp Query Content:", "value": whatsapp_query.content if whatsapp_query else "N/A"},
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
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON in request body: %s", e)
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logging.error(f"Error in assign_task: {e}")
            return JsonResponse({'error': 'An error occurred while assigning the task'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)





@csrf_exempt
def fetch_task_details(request, email_query_id):

    print("email query id", email_query_id)
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
            tasks = Task.objects.select_related('email_query', 'whatsapp_query', 'assigned_agent', 'assigned_team').all()
            task_list = []
            for task in tasks:
                email_query = task.email_query
                whatsapp_query = task.whatsapp_query
                email_history = []
                whatsapp_history = []

                # Fetch email history only if email_query is not None
                if email_query:
                    email_history = EmailReply.objects.filter(email_query=email_query).values(
                        'id', 'content', 'sent_at', 'responder__user__first_name', 'responder__user__last_name'
                    )

                # Fetch WhatsApp history only if whatsapp_query is not None
                if whatsapp_query:
                    whatsapp_history = WhatsAppReply.objects.filter(message=whatsapp_query).values(
                        'id', 'content', 'sent_at'
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
                        'id': email_query.id if email_query else None,
                        'subject': email_query.subject if email_query else None,
                        'content': email_query.content if email_query else None,
                        'received_at': email_query.received_at.strftime('%Y-%m-%d %H:%M:%S') if email_query else None,
                        'customer_email': email_query.customer.email if email_query else None,
                    } if email_query else None,
                    'whatsapp_query': {
                        'id': whatsapp_query.id if whatsapp_query else None,
                        'content': whatsapp_query.content if whatsapp_query else None,
                        'received_at': whatsapp_query.received_at.strftime('%Y-%m-%d %H:%M:%S') if whatsapp_query else None,
                        'customer_name': whatsapp_query.customer.name if whatsapp_query else None,
                        'customer_phone': whatsapp_query.customer.phone_number if whatsapp_query else None,
                    } if whatsapp_query else None,
                    'email_history': list(email_history),
                    'whatsapp_history': list(whatsapp_history),
                })
            return JsonResponse({'status': 'success', 'tasks': task_list})
        except Exception as e:
            logger.error(f"Error in fetch_tasks_with_email_history: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)