from django import forms
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

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
class GlobalEmailTemplateAdmin(SummernoteModelAdmin):
    summernote_fields = ("template",)


class EmailTemplateAdmin(SummernoteModelAdmin):
    summernote_fields = ("template",)


admin.site.register(GlobalEmailTemplate, GlobalEmailTemplateAdmin)
admin.site.register(GlobalEmailCampaign)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailCampaign)
admin.site.register(EmailQueue)
admin.site.register(SesEmailTemplate)
admin.site.register(SesEmailTemplateMarketPlace)
