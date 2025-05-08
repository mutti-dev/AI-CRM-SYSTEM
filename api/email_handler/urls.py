from django.urls import path
from . import views as email_views

urlpatterns = [
    path('fetch-emails/', email_views.fetch_unread_emails, name='fetch_emails'),
    path('process-queries/', email_views.process_queries, name='process_queries'),
    path('reply-email/', email_views.reply_to_email, name='reply_email'),
    path('unread-emails/', email_views.fetch_unread_emails_from_db, name='fetch_unread_emails_from_db'),
    path('email-details/<int:id>/', email_views.fetch_email_details, name='fetch_email_details'),
    path('email-replies/<int:id>/', email_views.fetch_email_replies, name='fetch_email_replies'),
    path('download-attachment/<str:email_id>/<str:attachment_id>/', email_views.download_attachment, name='download_attachment'),
]
