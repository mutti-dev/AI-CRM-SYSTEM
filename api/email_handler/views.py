from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, make_aware
from .models import EmailQuery, FAQ, Task, EmailReply, EmailLog, Customer, FineTunedDataset, Agent, Team
from .gmail_integration.gmail_client import GmailClient
import json
import logging
from google import genai
from dotenv import load_dotenv
import os
import requests  # Add this import for sending HTTP requests
from datetime import datetime
import re  
from .genai import client  # Import the GenAI client

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

genai_client = genai.Client(api_key=GEMINI_API_KEY)
gmail_client = GmailClient()

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

def get_graph_access_token():
    """
    Authenticate with Microsoft Graph and get an access token.
    """
    tenant_id = "your-tenant-id"  # Replace with your Azure tenant ID
    client_id = "your-client-id"  # Replace with your Azure app client ID
    client_secret = "your-client-secret"  # Replace with your Azure app client secret
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def send_task_to_teams(access_token, team_id, channel_id, task_details):
    """
    Send task details to a Microsoft Teams channel using the Graph API.
    """
    url = f"{GRAPH_API_BASE_URL}/teams/{team_id}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    message = {
        "body": {
            "content": (
                f"<b>New Task Assigned</b><br>"
                f"<b>Title:</b> {task_details['title']}<br>"
                f"<b>Description:</b> {task_details['description']}<br>"
                f"<b>Assigned Agent:</b> {task_details['assigned_agent']}<br>"
                f"<b>Assigned Team:</b> {task_details['assigned_team']}<br>"
                f"<b>Due Date:</b> {task_details['due_date']}<br>"
            )
        }
    }

    response = requests.post(url, json=message, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Failed to send message to Teams: {response.status_code}, {response.text}")

@csrf_exempt
def fetch_unread_emails(request):
    if request.method == 'POST':
        emails = gmail_client.fetch_unread_emails()
        emails_fetched = 0
        valid_emails = []

        for email in emails:
            logging.debug("Processing email: %s", email)

            if 'threadId' not in email:
                logging.error("Missing 'threadId' in email: %s", email)
                continue

            # Extract the email address from the sender field
            sender_email = email.get('sender')
            match = re.search(r'<(.*?)>', sender_email)
            if match:
                sender_email = match.group(1)
            else:
                sender_email = sender_email.strip()

            logging.debug("Extracted sender email: %s", sender_email)

            # Check if the sender exists in the Customer table
            customer = Customer.objects.filter(email=sender_email).first()
            if customer:
                # Check if the email thread already exists
                existing_query = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).first()
                if existing_query:
                    logging.info("Email thread already exists: %s", email['threadId'])
                    continue

                # Create a new EmailQuery
                EmailQuery.objects.create(
                    customer=customer,
                    subject=email.get('subject', 'No Subject'),
                    content=email.get('body', ''),
                    received_at=now(),
                    gmail_thread_id=email['threadId']
                )
                emails_fetched += 1
                valid_emails.append(email)

                # Automatically send a reply using GenAI
                try:
                    # Fetch previous email content in the thread for context
                    previous_emails = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).values_list('content', flat=True)
                    thread_context = "\n\n".join(previous_emails)

                    # Generate a professional and friendly reply using GenAI
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"""
                        You are AI Mutti, a friendly and professional assistant from MaxRemind. 
                        Your job is to generate well-written, polite, and helpful email replies.
                        Respond to the following email in a clear, concise, and respectful tone. 
                        Keep the language simple, professional, and approachable—neither too formal nor too casual. 
                        Always make the sender feel acknowledged, understood, and supported.
                        Make sure the reply sounds human, empathetic, and solution-oriented. 
                        Avoid robotic phrasing or overly complex language.
                        Here is the email thread context:
                        \"\"\"{thread_context}\"\"\"
                        Here is the latest email content:
                        \"\"\"{email.get('body', '')}\"\"\"
                        Write a well-formatted and thoughtful reply:
                        """
                    )
                    reply_content = response.text

                    gmail_message_id = gmail_client.send_reply(
                        to_email=sender_email,
                        subject=f"Re: {email.get('subject', 'No Subject')}",
                        body=reply_content,
                        thread_id=email['threadId']
                    )
                    logging.info("Auto-reply sent for email: %s", email['threadId'])

                    # Save the reply in EmailReply
                    EmailReply.objects.create(
                        email_query=EmailQuery.objects.get(gmail_thread_id=email['threadId']),
                        content=reply_content,
                        sent_at=now(),
                        gmail_message_id=gmail_message_id
                    )
                except Exception as e:
                    logging.error("Failed to send auto-reply for email %s: %s", email['threadId'], e)
            else:
                logging.debug("Sender not found in Customer table: %s", sender_email)

        return JsonResponse({
            'status': 'success',
            'emails_fetched': emails_fetched,
            'total_unread_emails_fetched': len(valid_emails),
            'emails': valid_emails
        })
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def process_queries(request):
    if request.method == 'POST':
        queries = EmailQuery.objects.filter(is_replied=False)
        processed_queries = []

        # Fetch predefined company information (FAQs or other data)
        company_info = FAQ.objects.values_list('keywords', 'answer')

        for query in queries:
            try:
                # Check if the query matches any predefined company information
                matched = False
                for keywords, answer in company_info:
                    keyword_list = [kw.strip().lower() for kw in keywords.split(',')]
                    if any(kw in query.content.lower() for kw in keyword_list):
                        # If a match is found, use the predefined answer
                        reply_content = answer
                        matched = True
                        break

                if not matched:
                    # If no match is found, send a generic acknowledgment response
                    reply_content = (
                        "Thank you for reaching out to us. "
                        "We have received your query and will get back to you shortly."
                    )

                # Send the reply via Gmail
                gmail_message_id = gmail_client.send_reply(
                    to_email=query.customer.email,
                    subject=f"Re: {query.subject}",
                    body=reply_content,
                    thread_id=query.gmail_thread_id
                )

                # Save the reply in the database
                EmailReply.objects.create(
                    email_query=query,
                    content=reply_content,
                    sent_at=now(),
                    gmail_message_id=gmail_message_id
                )

                # Mark the query as replied
                query.is_replied = True
                query.save()

                processed_queries.append({
                    'id': query.id,
                    'subject': query.subject,
                    'is_replied': query.is_replied,
                })
            except Exception as e:
                logging.error(f"Error processing query {query.id}: {e}")

        return JsonResponse({'status': 'success', 'processed_queries': processed_queries})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def assign_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print("data", data)

        # Parse and make the due_date timezone-aware
        due_date = None
        if data.get('due_date'):
            try:
                naive_due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
                due_date = make_aware(naive_due_date)  # Convert to timezone-aware datetime
            except ValueError as e:
                logging.error(f"Invalid due_date format: {e}")

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
        # https://outlook.office.com/webhook/your-correct-webhook-url
        try:
            webhook_url = "https://pern.webhook.office.com/webhookb2/b6bdde7c-c22b-46b5-bf7a-d4a02cc0daf8@75df096c-8b72-48e4-9b91-cbf79d87ee3a/IncomingWebhook/417f836e910844b282c2ce58e84b23ce/c8dba7ff-6bfd-4f06-92f2-fa8f96b5e923/V2jUtKRMbzuWaUuFvhaYcccWVEUY6kDSixc-WWxk5WqPk1"  # Corrected webhook URL
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
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def reply_to_email(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email_query = EmailQuery.objects.get(id=data['email_query_id'])
        reply_content = data['content']
        gmail_message_id = gmail_client.send_reply(
            to_email=email_query.customer.email,
            subject=f"Re: {email_query.subject}",
            body=reply_content,
            thread_id=email_query.gmail_thread_id
        )
        EmailReply.objects.create(
            email_query=email_query,
            content=reply_content,
            sent_at=now(),
            gmail_message_id=gmail_message_id
        )
        email_query.is_replied = True
        email_query.save()
        return JsonResponse({'status': 'success', 'gmail_message_id': gmail_message_id})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def dashboard_data(request):
    if request.method == 'GET':
        queries = EmailQuery.objects.all().count()
        replied_queries = EmailQuery.objects.filter(is_replied=True).count()
        complex_queries = EmailQuery.objects.filter(is_complex=True).count()
        tasks = Task.objects.all().count()
        logs = EmailLog.objects.all().count()
        return JsonResponse({
            'queries': queries,
            'replied_queries': replied_queries,
            'complex_queries': complex_queries,
            'tasks': tasks,
            'logs': logs
        })
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_customers(request):
    if request.method == 'GET':
        customers = Customer.objects.values('email', 'name')
        return JsonResponse({'status': 'success', 'customers': list(customers)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_unread_emails_from_db(request):
    if request.method == 'GET':
        unread_emails = EmailQuery.objects.filter(is_replied=False).values(
            'id', 
            'subject', 
            'customer__email', 
            'customer__name',  # Include customer name
            'received_at'
        )
        return JsonResponse({'status': 'success', 'emails': list(unread_emails)})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_email_details(request, id):
    if request.method == 'GET':
        try:
            email = EmailQuery.objects.get(id=id)
            email_details = {
                'id': email.id,
                'subject': email.subject,
                'sender': email.customer.email,
                'body': email.content,
                'received_at': email.received_at,
            }
            return JsonResponse({'status': 'success', 'email': email_details})
        except EmailQuery.DoesNotExist:
            return JsonResponse({'error': 'Email not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_email_replies(request, id):
    if request.method == 'GET':
        try:
            email_query = EmailQuery.objects.get(id=id)
            replies = EmailReply.objects.filter(email_query=email_query).values('id', 'content', 'sent_at')
            return JsonResponse({'status': 'success', 'replies': list(replies)})
        except EmailQuery.DoesNotExist:
            return JsonResponse({'error': 'Email not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

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
            return JsonResponse({'status': 'success', 'dataset_id': dataset.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_agents(request):
    if request.method == 'GET':
        agents = Agent.objects.values('id', 'user__first_name', 'user__last_name')
        agent_list = [
            {'id': agent['id'], 'name': f"{agent['user__first_name']} {agent['user__last_name']}"}
            for agent in agents
        ]
        print("agent",agent_list)
        return JsonResponse({'status': 'success', 'agents': agent_list})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_teams(request):
    if request.method == 'GET':
        teams = Team.objects.values('id', 'name')
        return JsonResponse({'status': 'success', 'teams': list(teams)})
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








