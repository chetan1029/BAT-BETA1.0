from django.contrib import admin

from bat.autoemail.models import EmailCampaign, EmailTemplate

# Register your models here.

admin.site.register(EmailTemplate)
admin.site.register(EmailCampaign)
