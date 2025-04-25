from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from ..whatsapp_integration.whatsapp_client import WhatsAppClient
from email_handler.models import Customer, WhatsAppMessage  # Import the Customer model
import logging
import json
from datetime import datetime
import pytz
from django.utils.timezone import make_aware

whatsapp_client = WhatsAppClient()
logger = logging.getLogger(__name__)












@csrf_exempt
@require_POST
def fetch_whatsapp_messages(request):
    try:
        # Fetch all messages
        messages = whatsapp_client.fetch_all_messages()
        raw_data = messages.get("data", {}).get("data", [])

        saved_messages = []

        for item in raw_data:
            whatsapp_id = item.get("id", {}).get("_serialized", "")
            user_id = item.get("id", {}).get("user", "")
            last_message = item.get("lastMessage", {}).get("_data", {}).get("body", "")
            timestamp = item.get("timestamp", None)

            if not user_id or not timestamp or not last_message:
                continue

            received_at = make_aware(datetime.fromtimestamp(int(timestamp)))

            # Match using phone number only (user_id)
            customer = Customer.objects.filter(phone_number=user_id).first()
            if not customer:
                logger.info(f"No customer found for phone: {user_id}")
                continue

            # Save or update message
            msg, created = WhatsAppMessage.objects.update_or_create(
                whatsapp_message_id=whatsapp_id,
                defaults={
                    
                    'customer': customer,
                    'thread_id': whatsapp_id.split("@")[0],
                    'content': last_message,
                    'received_at': received_at
                }
            )

            if created:
                saved_messages.append({
                    'chat_id': whatsapp_id,
                    'phone': user_id,
                    'message': last_message,
                    'timestamp': received_at
                })

        return JsonResponse({
            'status': 'success',
            'saved_count': len(saved_messages),
            'saved_messages': saved_messages
        })

    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)








@csrf_exempt
@require_POST
def send_messages(request):
    try:
        response = whatsapp_client.send_message()
        return JsonResponse({'status': 'success', 'response': response})
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    








@csrf_exempt
@require_POST
def get_chat_by_id(request):
    try:
        data = json.loads(request.body)
        chat_id = data.get('chatId')
        if not chat_id:
            return JsonResponse({'status': 'error', 'error': 'chatId not provided'}, status=400)
        response = whatsapp_client.get_chat_by_id(chat_id)
        return JsonResponse({'status': 'success', 'response': response})
    except Exception as e:
        logger.error(f"Error getting chat: {e}")
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)












@csrf_exempt
@require_POST
def get_whatsapp_messages_control(request):
    """
    Receive a JSON payload from the frontend to control the parameters for fetching messages.
    Uses whatsapp_client.fetch_messages() with overridden payload.
    """
    try:
        req_payload = json.loads(request.body)
        print(f"Received payload: {req_payload}")
    except Exception as e:
        logger.error(f"Error parsing payload: {e}")
        req_payload = {}
        
    payload = {
        "chatId": req_payload.get("chatId", whatsapp_client.chat_id),
        "limit": req_payload.get("limit", 10),

        "fromMe": req_payload.get("fromMe", False),
        "includeMedia": req_payload.get("includeMedia", False)
    }
    # Temporarily override the client's payload
    original_payload = whatsapp_client.payload
    whatsapp_client.payload = payload
    result = whatsapp_client.fetch_messages()
    whatsapp_client.payload = original_payload  # restore original payload
    
    if result:
        return JsonResponse({"status": "success", "payload": payload, "data": result})
    else:
        return JsonResponse({"status": "error", "payload": payload, "error": "Failed to fetch messages"}, status=500)





@csrf_exempt
def receive_wa_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            value = data['entry'][0]['changes'][0]['value']
            message_data = value['messages'][0]
            contact_data = value['contacts'][0]

            wa_id = contact_data['wa_id']  # Customer's WhatsApp number
            whatsapp_message_id = message_data['id']
            message_body = message_data['text']['body']
            timestamp = int(message_data['timestamp'])

            # Convert timestamp to datetime
            
            received_at = make_aware(datetime.fromtimestamp(timestamp))

            # Look up customer by wa_id
            try:
                customer = Customer.objects.get(phone_number=wa_id)
            except Customer.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': f'Customer with phone {wa_id} not found'}, status=404)

            # Avoid duplicate messages
            if WhatsAppMessage.objects.filter(whatsapp_message_id=whatsapp_message_id).exists():
                return JsonResponse({'status': 'duplicate', 'message': 'Message already exists'})

            # Save message
            WhatsAppMessage.objects.create(
                customer=customer,
                thread_id=value.get('metadata', {}).get('display_phone_number', 'unknown'),
                content=message_body,
                received_at=received_at,
                whatsapp_message_id=whatsapp_message_id
            )

            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)






@require_GET
def get_all_whatsapp_messages(request):
    messages = WhatsAppMessage.objects.all()
    data = []
    for msg in messages:
        data.append({
            'id': msg.id,
            'whatsapp_message_id': msg.whatsapp_message_id,
            'phone': msg.customer.phone_number if msg.customer else "",
            'customer_name': msg.customer.name if msg.customer else "",  # added customer name
            'message': msg.content,
            'received_at': msg.received_at.isoformat() if msg.received_at else ""
        })
    return JsonResponse({'status': 'success', 'messages': data})


@csrf_exempt
@require_POST
def send_custom_message_view(request):
    try:
        data = json.loads(request.body)
        print(f"Received payload: {data}")
        chat_id = data.get("chatId")
        message = data.get("replyContent")
        if not chat_id or not message:
            return JsonResponse({"status": "error", "error": "chatId and message are required"}, status=400)
        response = whatsapp_client.send_custom_message(chat_id, message)
        if response:
            return JsonResponse({"status": "success", "data": response})
        else:
            return JsonResponse({"status": "error", "error": "Failed to send custom message"}, status=500)
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)
