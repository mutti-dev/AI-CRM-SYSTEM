from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from api.integrations.whatsapp_integration.whatsapp_client import WhatsAppClient
from customers.models import Customer
from .models import WhatsAppMessage, WhatsAppReply
import json
from datetime import datetime
import pytz
from django.utils.timezone import make_aware
from ai_integration.chat_history import client, MODEL_NAME  # Updated import for AI responses
from ai_integration.prompts import generate_whatsapp_reply_prompt
from colorama import Fore, Style  # Import colorama for colored logs
from uuid import uuid4
import logging

whatsapp_client = WhatsAppClient()
logger = logging.getLogger(__name__)


def sanitize_message(message):
    # Replace or remove potentially problematic content
    prohibited_words = ["jailbreak", "bypass", "hack"]
    for word in prohibited_words:
        message = message.replace(word, "[REDACTED]")
    return message


@csrf_exempt
@require_POST
def fetch_whatsapp_messages(request):
    try:
        logger.info(Fore.CYAN + "Fetching WhatsApp messages..." + Style.RESET_ALL)

        # Fetch all messages
        messages = whatsapp_client.fetch_all_messages()
        raw_data = messages.get("data", {}).get("data", [])

        logger.info(
            Fore.GREEN + f"Fetched {len(raw_data)} message threads." + Style.RESET_ALL
        )

        saved_messages = []

        for item in raw_data:
            whatsapp_id = item.get("id", {}).get("_serialized", "")
            user_id = item.get("id", {}).get("user", "")
            last_message_data = item.get("lastMessage", {}).get("_data", {})
            last_message = last_message_data.get("body", "")  # Ensure this is a string
            from_me = last_message_data.get("id", {}).get(
                "fromMe", False
            )  # Retrieve directly from last_message_data
            timestamp = item.get("timestamp", None)

            logger.info(
                Fore.YELLOW
                + f"Processing message: ID={whatsapp_id}, fromMe={from_me}, body={repr(last_message)}"
                + Style.RESET_ALL
            )

            # Skip messages sent by me
            if from_me:
                logger.info(
                    Fore.MAGENTA
                    + f"Skipping message sent by me: ID={whatsapp_id}"
                    + Style.RESET_ALL
                )
                continue

            if not user_id or not timestamp or not last_message:
                logger.warning(
                    Fore.RED
                    + f"Skipping incomplete message. user_id={user_id}, timestamp={timestamp}, body={repr(last_message)}"
                    + Style.RESET_ALL
                )
                continue

            received_at = make_aware(datetime.fromtimestamp(int(timestamp)))

            # Match using phone number only (user_id)
            customer = Customer.objects.filter(phone_number=user_id).first()
            if not customer:
                logger.info(
                    Fore.RED
                    + f"No customer found for phone: {user_id}"
                    + Style.RESET_ALL
                )
                continue

            # Check if the message already exists
            existing_message = WhatsAppMessage.objects.filter(thread_id=user_id).first()

            if existing_message:
                logger.info(
                    Fore.BLUE
                    + f"Message already exists: ID={whatsapp_id}, skipping."
                    + Style.RESET_ALL
                )
                continue

            # Save the message
            unique_message_id = f"{whatsapp_id}_{uuid4().hex[:8]}"
            msg = WhatsAppMessage.objects.create(
                whatsapp_message_id=unique_message_id,
                customer=customer,
                thread_id=whatsapp_id.split("@")[0],
                content=last_message,
                received_at=received_at,
                is_replied=False,  # Initially set to False
            )
            create = True

            logger.info(
                Fore.GREEN
                + f"Message saved for customer: {customer.name}, ID={whatsapp_id}"
                + Style.RESET_ALL
            )

            saved_messages.append(
                {
                    "customer_name": customer.name,
                    "chat_id": whatsapp_id,
                    "phone": user_id,
                    "message": last_message,
                    "timestamp": received_at.isoformat(),
                }
            )

            if create:

                # Send automated reply
                try:
                    sanitized_message = sanitize_message(last_message)
                    prompt = generate_whatsapp_reply_prompt(
                        customer.name, sanitized_message
                    )

                    # Log the sanitized prompt
                    logger.debug(f"Sanitized prompt: {prompt}")

                    # Use the correct 'messages' format for the OpenAI client
                    messages = [
                        {
                            "role": "system",
                            "content": "You are an AI assistant helping with WhatsApp replies.",
                        },
                        {"role": "user", "content": prompt},
                    ]
                    gen_response = client.chat.completions.create(
                        model=MODEL_NAME, messages=messages
                    )
                    # Correctly access the content of the response
                    reply_content = gen_response.choices[0].message.content.strip()

                    # Send the reply via WhatsApp
                    whatsapp_client.send_custom_message(whatsapp_id, reply_content)
                    logger.info(
                        Fore.CYAN + f"AI reply sent to {whatsapp_id}" + Style.RESET_ALL
                    )

                    # Update the message as replied
                    msg.is_replied = True
                    msg.save()

                    # Save the reply in WhatsAppReply model
                    WhatsAppReply.objects.create(
                        message=msg,
                        content=reply_content,
                        whatsapp_message_id=f"{unique_message_id}_reply",
                    )

                    

                except Exception as gen_err:
                    if "content_filter" in str(gen_err):
                        logger.error(
                            Fore.RED
                            + f"Content filter triggered for {user_id}: {gen_err}"
                            + Style.RESET_ALL
                        )
                        continue  # Skip this message and move to the next
                    else:
                        logger.error(
                            Fore.RED
                            + f"Error generating or sending AI reply for {user_id}: {gen_err}"
                            + Style.RESET_ALL
                        )

        logger.info(
            Fore.GREEN
            + f"Done processing messages. Saved: {len(saved_messages)}"
            + Style.RESET_ALL
        )

        return JsonResponse(
            {
                "status": "success",
                "saved_count": len(saved_messages),
                "saved_messages": saved_messages,
            }
        )

    except Exception as e:
        logger.error(
            Fore.RED + f"Error fetching messages: {e}" + Style.RESET_ALL, exc_info=True
        )
        return JsonResponse({"status": "error", "error": str(e)}, status=500)


@csrf_exempt
@require_POST
def get_chat_by_id(request):
    try:
        data = json.loads(request.body)
        chat_id = data.get("chatId")
        if not chat_id:
            return JsonResponse(
                {"status": "error", "error": "chatId not provided"}, status=400
            )
        response = whatsapp_client.get_chat_by_id(chat_id)
        return JsonResponse({"status": "success", "response": response})
    except Exception as e:
        logger.error(f"Error getting chat: {e}")
        return JsonResponse({"status": "error", "error": str(e)}, status=500)


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
        "includeMedia": req_payload.get("includeMedia", False),
    }
    # Temporarily override the client's payload
    original_payload = whatsapp_client.payload
    whatsapp_client.payload = payload
    result = whatsapp_client.fetch_messages()
    whatsapp_client.payload = original_payload  # restore original payload

    if result:
        return JsonResponse({"status": "success", "payload": payload, "data": result})
    else:
        return JsonResponse(
            {
                "status": "error",
                "payload": payload,
                "error": "Failed to fetch messages",
            },
            status=500,
        )


@require_GET
def get_all_whatsapp_messages(request):
    messages = WhatsAppMessage.objects.all()
    data = []
    for msg in messages:
        data.append(
            {
                "id": msg.id,
                "whatsapp_message_id": msg.whatsapp_message_id,
                "phone": msg.customer.phone_number if msg.customer else "",
                "customer_name": (
                    msg.customer.name if msg.customer else ""
                ),  # added customer name
                "message": msg.content,
                "received_at": msg.received_at.isoformat() if msg.received_at else "",
            }
        )
    return JsonResponse({"status": "success", "messages": data})


@csrf_exempt
@require_POST
def send_custom_message_view(request):
    try:
        data = json.loads(request.body)
        print(f"Received payload: {data}")
        chat_id = data.get("chatId")
        message = data.get("replyContent")
        if not chat_id or not message:
            return JsonResponse(
                {"status": "error", "error": "chatId and message are required"},
                status=400,
            )
        response = whatsapp_client.send_custom_message(chat_id, message)
        if response:
            return JsonResponse({"status": "success", "data": response})
        else:
            return JsonResponse(
                {"status": "error", "error": "Failed to send custom message"},
                status=500,
            )
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)
