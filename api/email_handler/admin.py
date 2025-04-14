from django.contrib import admin
from .models import Team, Agent, Customer, FAQ, EmailQuery, EmailReply, Task, EmailLog, FineTunedDataset, WhatsAppReply, WhatsAppMessage

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'preferred_contact', 'created_at')
    search_fields = ('name', 'email', 'phone_number')
    list_filter = ('preferred_contact', 'created_at')

# Register other models
admin.site.register(Team)
admin.site.register(Agent)
admin.site.register(FAQ)
admin.site.register(EmailQuery)
admin.site.register(EmailReply)
admin.site.register(Task)
admin.site.register(EmailLog)
admin.site.register(FineTunedDataset)
admin.site.register(WhatsAppMessage)
admin.site.register(WhatsAppReply)
