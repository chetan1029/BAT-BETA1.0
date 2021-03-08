from django.contrib import admin

from bat.autoemail.models import EmailCampaign, EmailQueue, EmailTemplate

# Register your models here.

admin.site.register(EmailTemplate)
admin.site.register(EmailCampaign)
admin.site.register(EmailQueue)
