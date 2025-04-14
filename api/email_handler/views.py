from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now, make_aware
from .models import EmailQuery, FAQ, Task, EmailReply, EmailLog, Customer, FineTunedDataset, Agent, Team, WhatsAppMessage, WhatsAppReply
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
from .whatsapp_integration.whatsapp_client import WhatsAppClient

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

genai_client = genai.Client(api_key=GEMINI_API_KEY)
gmail_client = GmailClient()
whatsapp_client = WhatsAppClient()

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

# def get_graph_access_token():
#     """
#     Authenticate with Microsoft Graph and get an access token.
#     """
#     tenant_id = "your-tenant-id"  # Replace with your Azure tenant ID
#     client_id = "your-client-id"  # Replace with your Azure app client ID
#     client_secret = "your-client-secret"  # Replace with your Azure app client secret
#     token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

#     data = {
#         "grant_type": "client_credentials",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "scope": "https://graph.microsoft.com/.default",
#     }

#     response = requests.post(token_url, data=data)
#     response.raise_for_status()
#     return response.json()["access_token"]

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
def reply_to_email(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email_query = get_object_or_404(EmailQuery, id=data['email_query_id'])
            reply_content = data['content'].strip()
            message_id = data.get('message_id')
            
            if not reply_content:
                return JsonResponse({'error': 'Reply content cannot be empty'}, status=400)

            # Add email signature and format content
            formatted_content = f"{reply_content}\n\nBest regards,\nMaxRemind Team"
            
            # Retry mechanism for Gmail API
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    gmail_message_id = gmail_client.reply_to_thread(
                        to_email=email_query.customer.email,
                        subject=f"Re: {email_query.subject}",
                        body=formatted_content,
                        thread_id=email_query.gmail_thread_id,
                        message_id=message_id
                    )
                    
                    if gmail_message_id:
                        break
                    retry_count += 1
                except Exception as e:
                    logging.error(f"Retry {retry_count + 1} failed: {str(e)}")
                    retry_count += 1
                    if retry_count == max_retries:
                        raise

            if not gmail_message_id:
                raise Exception("Failed to send email after multiple retries")

            reply = EmailReply.objects.create(
                email_query=email_query,
                content=formatted_content,
                sent_at=now(),
                gmail_message_id=gmail_message_id
            )
            
            email_query.is_replied = True
            email_query.save()
            
            # Create success log
            EmailLog.objects.create(
                email_query=email_query,
                action='Replied',
                message=f"Reply sent successfully. Message ID: {gmail_message_id}"
            )
            
            return JsonResponse({
                'status': 'success',
                'reply': {
                    'id': reply.id,
                    'content': reply.content,
                    'sent_at': reply.sent_at.isoformat(),
                    'gmail_message_id': gmail_message_id
                }
            })
            
        except Exception as e:
            logging.error(f"Error sending reply: {str(e)}")
            # Create error log
            EmailLog.objects.create(
                email_query=email_query if 'email_query' in locals() else None,
                action='Failed',
                message=f"Reply failed: {str(e)}"
            )
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send reply. Please try again.',
                'error': str(e)
            }, status=500)
    
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
            # Fetch the complete thread from Gmail
            thread_messages = gmail_client.get_thread(email.gmail_thread_id)
            
            email_details = {
                'id': email.id,
                'subject': email.subject,
                'sender': email.customer.email,
                'body': email.content,
                'received_at': email.received_at,
                'thread_id': email.gmail_thread_id,
                'thread_messages': thread_messages
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

@csrf_exempt
def fetch_whatsapp_messages(request):
    if request.method == 'POST':
        try:
            logging.info("Starting to fetch WhatsApp messages")
            messages = whatsapp_client.fetch_unread_messages()
            messages_fetched = 0
            valid_messages = []

            for message in messages:
                logging.debug(f"Processing WhatsApp message: {message}")
                
                # Check if customer exists by phone number
                phone_number = message.get('from', '').strip()
                if not phone_number:
                    logging.error("Message has no 'from' number")
                    continue

                customer = Customer.objects.filter(phone_number=phone_number).first()
                
                # Create customer if doesn't exist
                if not customer:
                    logging.info(f"Creating new customer for number: {phone_number}")
                    customer = Customer.objects.create(
                        phone_number=phone_number,
                        preferred_contact='whatsapp'
                    )

                # Check for existing message to avoid duplicates
                existing_message = WhatsAppMessage.objects.filter(
                    whatsapp_message_id=message['id']
                ).exists()

                if not existing_message:
                    whatsapp_message = WhatsAppMessage.objects.create(
                        customer=customer,
                        thread_id=message.get('thread_id', ''),
                        content=message.get('content', ''),
                        received_at=now(),
                        whatsapp_message_id=message['id']
                    )
                    
                    # Generate AI reply
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=f"""
                            Generate a friendly WhatsApp reply to: {message.get('content', '')}
                            Keep it concise and conversational.
                            """
                        )
                        reply_content = response.text

                        reply = whatsapp_client.send_reply(
                            to_number=phone_number,
                            message=reply_content,
                            thread_id=message.get('thread_id', '')
                        )

                        if reply:
                            WhatsAppReply.objects.create(
                                message=whatsapp_message,
                                content=reply_content,
                                whatsapp_message_id=reply['message_id']
                            )
                            messages_fetched += 1
                            valid_messages.append({
                                'id': whatsapp_message.id,
                                'from': phone_number,
                                'content': message.get('content', ''),
                                'received_at': whatsapp_message.received_at.isoformat(),
                                'thread_id': message.get('thread_id', ''),
                                'reply': reply_content
                            })
                            logging.info(f"Successfully processed message {message['id']}")
                    except Exception as e:
                        logging.error(f"Error processing WhatsApp message: {str(e)}")
                else:
                    logging.debug(f"Message {message['id']} already exists")

            return JsonResponse({
                'status': 'success',
                'messages_fetched': messages_fetched,
                'messages': valid_messages,
                'debug_info': {
                    'total_messages_received': len(messages),
                    'total_valid_messages': len(valid_messages)
                }
            })
        except Exception as e:
            logging.error(f"Error in fetch_whatsapp_messages: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'error': str(e),
                'message': 'Failed to fetch WhatsApp messages'
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_whatsapp_details(request, id):
    if request.method == 'GET':
        try:
            message = WhatsAppMessage.objects.get(id=id)
            thread_messages = whatsapp_client.get_thread(message.thread_id)
            
            message_details = {
                'id': message.id,
                'thread_id': message.thread_id,
                'customer_name': message.customer.name,
                'phone_number': message.customer.phone_number,
                'content': message.content,
                'received_at': message.received_at,
                'thread_messages': thread_messages
            }
            return JsonResponse({'status': 'success', 'message': message_details})
        except WhatsAppMessage.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def reply_to_whatsapp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = WhatsAppMessage.objects.get(id=data['message_id'])
            content = data['content'].strip()
            
            if not content:
                return JsonResponse({'error': 'Message content cannot be empty'}, status=400)
            
            reply = whatsapp_client.send_reply(
                to_number=message.customer.phone_number,
                message=content,
                thread_id=message.thread_id
            )
            
            if reply:
                whatsapp_reply = WhatsAppReply.objects.create(
                    message=message,
                    content=content,
                    whatsapp_message_id=reply['message_id']
                )
                
                return JsonResponse({
                    'status': 'success',
                    'reply': {
                        'id': whatsapp_reply.id,
                        'content': whatsapp_reply.content,
                        'sent_at': whatsapp_reply.sent_at.isoformat(),
                    }
                })
            else:
                raise Exception("Failed to send WhatsApp reply")
                
        except Exception as e:
            logging.error(f"Error sending WhatsApp reply: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send reply. Please try again.',
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_whatsapp_thread(request, thread_id):
    if request.method == 'GET':
        try:
            messages = WhatsAppMessage.objects.filter(thread_id=thread_id).order_by('received_at')
            replies = WhatsAppReply.objects.filter(message__thread_id=thread_id).order_by('sent_at')
            
            thread_data = {
                'thread_id': thread_id,
                'messages': list(messages.values('id', 'content', 'received_at', 'customer__name')),
                'replies': list(replies.values('id', 'content', 'sent_at'))
            }
            
            return JsonResponse({'status': 'success', 'thread': thread_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_unread_whatsapp(request):
    if request.method == 'GET':
        unread_messages = WhatsAppMessage.objects.filter(is_replied=False).values(
            'id',
            'content',
            'customer__name',
            'customer__phone_number',
            'received_at'
        )
        return JsonResponse({
            'status': 'success',
            'messages': list(unread_messages)
        })
    return JsonResponse({'error': 'Invalid request method'}, status=400)








