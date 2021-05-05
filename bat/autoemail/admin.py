from django.contrib import admin

from bat.autoemail.models import (
    EmailCampaign,
    EmailQueue,
    EmailTemplate,
    GlobalEmailCampaign,
    GlobalEmailTemplate,
    SesEmailTemplate,
    SesEmailTemplateMarketPlace,
)

# Register your models here.

admin.site.register(GlobalEmailTemplate)
admin.site.register(GlobalEmailCampaign)
admin.site.register(EmailTemplate)
admin.site.register(EmailCampaign)
admin.site.register(EmailQueue)
admin.site.register(SesEmailTemplate)
admin.site.register(SesEmailTemplateMarketPlace)
