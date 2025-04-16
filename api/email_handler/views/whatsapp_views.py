from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils.timezone import now
from ..models import Customer, WhatsAppMessage, WhatsAppReply
from ..whatsapp_integration.whatsapp_client import WhatsAppClient
from ..genai import client
import json
import logging

whatsapp_client = WhatsAppClient()
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def fetch_whatsapp_messages(request):
    try:
        logger.info("Starting to fetch WhatsApp messages")
        messages = whatsapp_client.fetch_unread_messages()
        messages_fetched = 0
        valid_messages = []

        for message in messages:
            phone_number = message.get('from') or message.get('sender') or ''
            phone_number = phone_number.strip()
            if not phone_number:
                logger.error("Message has no 'from' number")
                continue

            customer, _ = Customer.objects.get_or_create(
                phone_number=phone_number,
                defaults={'preferred_contact':'whatsapp'}
            )

            message_id = message.get('id')
            if not message_id:
                logger.warning('No message id present')
                continue

            if not WhatsAppMessage.objects.filter(whatsapp_message_id=message_id).exists():
                whatsapp_message = WhatsAppMessage.objects.create(
                    customer=customer,
                    thread_id=message.get('thread_id', ''),
                    content=message.get('content', ''),
                    received_at=now(),
                    whatsapp_message_id=message_id
                )

                reply_content = None
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"""
                        Generate a friendly WhatsApp reply to: {message.get('content', '')}
                        Keep it concise and conversational.
                        """
                    )
                    reply_content = response.text.strip()

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
                        whatsapp_message.is_replied = True
                        whatsapp_message.save(update_fields=['is_replied'])

                        messages_fetched += 1
                        valid_messages.append({
                            'id': whatsapp_message.id,
                            'from': phone_number,
                            'content': message.get('content', ''),
                            'received_at': whatsapp_message.received_at.isoformat(),
                            'thread_id': message.get('thread_id', ''),
                            'reply': reply_content
                        })
                except Exception as e:
                    logger.error(f"Error generating or sending reply: {str(e)}")

            else:
                logger.debug(f"Message {message_id} already exists")

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
        logger.error(f"Error in fetch_whatsapp_messages: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'message': 'Failed to fetch WhatsApp messages'
        }, status=500)

@csrf_exempt
@require_GET
def fetch_whatsapp_details(request, id):
    try:
        message = WhatsAppMessage.objects.get(pk=id)
        thread_messages = whatsapp_client.get_thread(message.thread_id)

        message_details = {
            'id': message.id,
            'thread_id': message.thread_id,
            'customer_name': getattr(message.customer, 'name', ''),
            'phone_number': message.customer.phone_number,
            'content': message.content,
            'received_at': message.received_at.isoformat(),
            'thread_messages': thread_messages
        }
        return JsonResponse({'status': 'success', 'message': message_details})
    except WhatsAppMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in fetch_whatsapp_details: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def reply_to_whatsapp(request):
    try:
        data = json.loads(request.body)
        msg_id = data.get('message_id')
        content = (data.get('content') or '').strip()
        if not content:
            return JsonResponse({'error': 'Message content cannot be empty'}, status=400)

        message = WhatsAppMessage.objects.get(pk=msg_id)
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
            message.is_replied = True
            message.save(update_fields=['is_replied'])
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
    except WhatsAppMessage.DoesNotExist:
        return JsonResponse({'error': 'Original message not found'}, status=404)
    except Exception as e:
        logger.error(f"Error sending WhatsApp reply: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_GET
def fetch_whatsapp_thread(request, thread_id):
    try:
        messages = WhatsAppMessage.objects.filter(thread_id=thread_id).order_by('received_at')
        replies = WhatsAppReply.objects.filter(message__thread_id=thread_id).order_by('sent_at')

        thread_data = {
            'thread_id': thread_id,
            'messages': [{
                'id': m.id,
                'content': m.content,
                'received_at': m.received_at.isoformat(),
                'customer_name': getattr(m.customer, 'name', '')
            } for m in messages],
            'replies': [{
                'id': r.id,
                'content': r.content,
                'sent_at': r.sent_at.isoformat(),
            } for r in replies]
        }

        return JsonResponse({'status': 'success', 'thread': thread_data})
    except Exception as e:
        logger.error(f"Error in fetch_whatsapp_thread: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_GET
def fetch_unread_whatsapp(request):
    unread_messages = WhatsAppMessage.objects.filter(is_replied=False).values(
        'id',
        'content',
        'customer__name',
        'customer__phone_number',
        'received_at'
    )
    result = []
    for msg in unread_messages:
        msg['received_at'] = msg['received_at'].isoformat() if msg['received_at'] else None
        result.append(msg)

    return JsonResponse({
        'status': 'success',
        'messages': result
    })

@csrf_exempt
@require_GET
def test_whatsapp_connection(request):
    try:
        status = whatsapp_client.fetch_unread_messages()
        return JsonResponse({
            'status': 'success',
            'connection_test': 'ok',
            'api_response': status
        })
    except Exception as e:
        logger.error(f"Error in test_whatsapp_connection: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)