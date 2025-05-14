# @csrf_exempt
# def fetch_unread_emails(request):
#     if request.method == 'POST':
#         emails = gmail_client.fetch_unread_emails()
#         outlook_emails = outlook_client.fetch_unread_emails()
#         emails_fetched = 0
#         valid_emails = []
#
#         for email in emails:
#             # logging.debug("Processing email: %s", email)
#
#             if 'threadId' not in email:
#                 logging.error("Missing 'threadId' in email: %s", email)
#                 continue
#
#             # Extract the email address from the sender field
#             sender_email = email.get('sender')
#             match = re.search(r'<(.*?)>', sender_email)
#             if match:
#                 sender_email = match.group(1)
#             else:
#                 sender_email = sender_email.strip()
#
#             # logging.debug("Extracted sender email: %s", sender_email)
#
#             # Check if the sender exists in the Customer table
#             customer = Customer.objects.filter(email=sender_email).first()
#             if customer:
#                 # Check if the email thread already exists
#                 existing_query = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).first()
#                 if existing_query:
#                     logging.info("Email thread already exists: %s", email['threadId'])
#                     continue  # Skip creating a new EmailQuery
#
#                 # Create a new EmailQuery
#                 email_query = EmailQuery.objects.create(
#                     customer=customer,
#                     subject=email.get('subject', 'No Subject'),
#                     content=email.get('body', ''),
#                     received_at=now(),
#                     gmail_thread_id=email['threadId']
#                 )
#
#                 # Save attachments in the database
#                 for attachment in email.get('attachments', []):
#                     EmailAttachment.objects.create(
#                         email_query=email_query,
#                         filename=attachment['filename'],
#                         mime_type=attachment['mimeType'],
#                         size=attachment['size'],
#                         download_url=attachment['download_url']
#                     )
#
#                 emails_fetched += 1
#                 valid_emails.append(email)
#
#                 # Automatically send a reply using GenAI
#                 try:
#                     # Retry logic for network errors
#                     max_retries = 3
#                     retry_count = 0
#                     while retry_count < max_retries:
#                         try:
#                             # Fetch previous email content in the thread for context
#                             previous_emails = EmailQuery.objects.filter(gmail_thread_id=email['threadId']).values_list(
#                                 'content', flat=True)
#                             thread_context = "\n\n".join(previous_emails)
#                             prompt = generate_email_reply_prompt(thread_context, email.get('body', ''), customer.name)
#
#                             # Use the correct 'messages' format for the OpenAI client
#                             messages = [
#                                 {"role": "system", "content": "You are an AI assistant helping with email replies."},
#                                 {"role": "user", "content": prompt}
#                             ]
#                             response = client.chat.completions.create(
#                                 model=MODEL_NAME,
#                                 messages=messages
#                             )
#                             # Correctly access the content of the response
#                             reply_content = response.choices[0].message.content.strip()
#
#                             logging.debug("Generated reply content: %s", reply_content)
#
#                             gmail_message_id = gmail_client.send_reply(
#                                 to_email=sender_email,
#                                 subject=f"Re: {email.get('subject', 'No Subject')}",
#                                 body=reply_content,
#                                 thread_id=email['threadId']
#                             )
#                             logging.info("Auto-reply sent for email: %s", email['threadId'])
#
#                             # Save the reply in EmailReply
#                             EmailReply.objects.create(
#                                 email_query=EmailQuery.objects.get(gmail_thread_id=email['threadId']),
#                                 content=reply_content,
#                                 sent_at=now(),
#                                 gmail_message_id=gmail_message_id
#                             )
#                             break  # Exit retry loop on success
#                         except httpx.ConnectError as e:
#                             retry_count += 1
#                             logging.error(f"Connection error, retrying {retry_count}/{max_retries}: {e}")
#                             time.sleep(2)  # Wait before retrying
#                             if retry_count == max_retries:
#                                 raise
#                 except Exception as e:
#                     logging.error("Failed to send auto-reply for email %s: %s", email['threadId'], e)
#             else:
#                 # logging.debug("Sender not found in Customer table: %s", sender_email)
#                 print("Not found email")
#
#         return JsonResponse({
#             'status': 'success',
#             'emails_fetched': emails_fetched,
#             'total_unread_emails_fetched': len(valid_emails),
#             'emails': valid_emails
#         })
#     return JsonResponse({'error': 'Invalid request method'}, status=400)

