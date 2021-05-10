from ckeditor.widgets import CKEditorWidget
from django import forms
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


class GlobalEmailTemplateForm(forms.ModelForm):
    template = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = GlobalEmailTemplate
        fields = "__all__"


class GlobalEmailTemplateAdmin(admin.ModelAdmin):
    form = GlobalEmailTemplateForm


class EmailTemplateForm(forms.ModelForm):
    template = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = EmailTemplate
        fields = "__all__"


class EmailTemplateAdmin(admin.ModelAdmin):
    form = EmailTemplateForm


admin.site.register(GlobalEmailTemplate, GlobalEmailTemplateAdmin)
admin.site.register(GlobalEmailCampaign)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailCampaign)
admin.site.register(EmailQueue)
admin.site.register(SesEmailTemplate)
admin.site.register(SesEmailTemplateMarketPlace)
