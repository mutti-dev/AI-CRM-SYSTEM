from django.contrib import admin
from .models import Team, Agent, Customer, FAQ, EmailQuery, EmailReply, Task, EmailLog, FineTunedDataset

admin.site.register(Team)
admin.site.register(Agent)
admin.site.register(Customer)
admin.site.register(FAQ)
admin.site.register(EmailQuery)
admin.site.register(EmailReply)
admin.site.register(Task)
admin.site.register(EmailLog)
admin.site.register(FineTunedDataset)
