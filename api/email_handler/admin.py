from django.contrib import admin
from .models import  EmailQuery, EmailReply,  EmailLog,  EmailAttachment



admin.site.register(EmailQuery)
admin.site.register(EmailReply)
admin.site.register(EmailLog)
admin.site.register(EmailAttachment)

