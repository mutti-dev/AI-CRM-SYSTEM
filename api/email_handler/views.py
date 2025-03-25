from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import EmailQuery, FAQ, Task, EmailReply, EmailLog, Customer
from .gmail_integration.gmail_client import GmailClient
import json
import logging

gmail_client = GmailClient()

@csrf_exempt
def fetch_unread_emails(request):
    if request.method == 'POST':
        emails = gmail_client.fetch_unread_emails()
        emails_fetched = 0
        for email in emails:
            # Check if the email with the same gmail_thread_id already exists
            if not EmailQuery.objects.filter(gmail_thread_id=email['threadId']).exists():
                customer, _ = Customer.objects.get_or_create(email=email['sender'])
                EmailQuery.objects.create(
                    customer=customer,
                    subject=email['subject'],
                    content=email['body'],
                    received_at=now(),
                    gmail_thread_id=email['threadId']
                )
                emails_fetched += 1  # Increment only for new emails
            else:
                logging.debug("Duplicate email skipped: Thread ID %s", email['threadId'])
        return JsonResponse({'status': 'success', 'emails_fetched': emails_fetched})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def process_queries(request):
    if request.method == 'POST':
        queries = EmailQuery.objects.filter(is_replied=False)
        for query in queries:
            matched_faq = FAQ.objects.filter(keywords__icontains=query.content).first()
            if matched_faq:
                query.is_complex = False
                EmailReply.objects.create(
                    email_query=query,
                    content=matched_faq.answer,
                    sent_at=now(),
                    gmail_message_id=gmail_client.send_reply(
                        to_email=query.customer.email,
                        subject=f"Re: {query.subject}",
                        body=matched_faq.answer,
                        thread_id=query.gmail_thread_id
                    )
                )
                query.is_replied = True
            else:
                query.is_complex = True
            query.save()
        return JsonResponse({'status': 'success', 'processed_queries': queries.count()})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def assign_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email_query = EmailQuery.objects.get(id=data['email_query_id'])
        task = Task.objects.create(
            email_query=email_query,
            title=data['title'],
            description=data['description'],
            assigned_team_id=data.get('assigned_team_id'),
            assigned_agent_id=data.get('assigned_agent_id'),
            due_date=data.get('due_date')
        )
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
