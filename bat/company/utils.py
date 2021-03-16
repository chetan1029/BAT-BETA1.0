from collections import OrderedDict

from django.shortcuts import get_object_or_404

from rolepermissions.roles import RolesManager

from bat.company.models import Member, Company, CompanyPaymentTerms
from bat.setting.models import PaymentTerms
from bat.autoemail.models import GlobalEmailCampaign, GlobalEmailTemplate, EmailCampaign, EmailTemplate


def get_member(company_id=None, user_id=None, raise_exception=True):
    """
    get member based on company and user
    """
    if raise_exception:
        member = get_object_or_404(Member, company__id=company_id, user=user_id)
    else:
        member = Member.objects.filter(company__id=company_id, user=user_id).first()
    return member


def get_list_of_roles_permissions():
    """
    return list of roles available
    """
    all_roles = OrderedDict()
    for role in RolesManager.get_roles():
        role_name = role.get_name()

        all_roles[role_name] = {
            "permissions": [{'name': name, 'default': value} for name, value in getattr(role, 'available_permissions', {}).items()]
        }
    return all_roles


def get_list_of_roles():

    return list(get_list_of_roles_permissions().keys())


def get_list_of_permissions():
    permissions = []
    for role in RolesManager.get_roles():
        permissions.extend(list(role.permission_names_list()))
    return permissions


def set_default_company_payment_terms(company):
    """
    copy global payment terms to given company's setting payment terms.
    """
    if isinstance(company, Company):
        all_global_payment_terms = PaymentTerms.objects.all()
        if all_global_payment_terms.exists():
            for global_payment_term in all_global_payment_terms:
                data = {}
                data["company"] = company
                data["title"] = global_payment_term.title
                data["deposit"] = global_payment_term.deposit
                data["on_delivery"] = global_payment_term.on_delivery
                data["receiving"] = global_payment_term.receiving
                data["remaining"] = global_payment_term.remaining
                data["payment_days"] = global_payment_term.payment_days
                data["is_active"] = global_payment_term.is_active
                data["extra_data"] = global_payment_term.extra_data
                CompanyPaymentTerms.objects.create(**data)


def set_default_email_campaign_templates(company):
    """
    copy global email campaigns, and global email templates to given company's campaigns and email templates.
    """
    if isinstance(company, Company):
        def _get_kwargs_for_template(company, global_template):
            template_data = {}
            template_data["company"] = company
            template_data["name"] = global_template.name
            template_data["subject"] = global_template.subject
            template_data["default_cc"] = global_template.default_cc
            template_data["logo"] = global_template.logo
            template_data["attachment_file"] = global_template.attachment_file
            template_data["language"] = global_template.language
            template_data["template"] = global_template.template
            template_data["name"] = global_template.name
            template_data["name"] = global_template.name
            return template_data

        all_global_email_campaigns = GlobalEmailCampaign.objects.all()
        all_global_email_templates = GlobalEmailTemplate.objects.all()
        
        if all_global_email_campaigns.exists() and all_global_email_templates.exists():
            email_campaign_objects = []
            created_templates_id = []
            for global_email_campaigns in all_global_email_campaigns:
                data = {}
                data["company"] = company
                data["name"] = global_email_campaigns.name
                data["status"] = global_email_campaigns.status
                data["amazonmarketplace"] = global_email_campaigns.amazonmarketplace
                data["order_status"] = global_email_campaigns.order_status
                data["channel"] = global_email_campaigns.channel
                data["schedule"] = global_email_campaigns.schedule
                data["schedule_days"] = global_email_campaigns.schedule_days
                data["buyer_purchase_count"] = global_email_campaigns.buyer_purchase_count
                data["exclude_orders"] = global_email_campaigns.exclude_orders
                data["extra_data"] = global_email_campaigns.extra_data

                # copy email template
                template_data = {}
                global_template = all_global_email_templates.get(
                    pk=global_email_campaigns.emailtemplate_id)
                template_data = _get_kwargs_for_template(company, global_template)
                template = EmailTemplate.objects.create(**template_data)
                created_templates_id.append(global_email_campaigns.emailtemplate_id)

                data["emailtemplate"] = template
                email_campaign_objects.append(EmailCampaign(**data))

            EmailCampaign.objects.bulk_create(email_campaign_objects)

            remaining_global_email_templates = all_global_email_templates.exclude(
                pk__in=created_templates_id)

            if remaining_global_email_templates.exists():
                email_template_objects = []
                for global_email_template in remaining_global_email_templates:
                    template_data = _get_kwargs_for_template(company, global_email_template)
                    email_template_objects.append(EmailTemplate(**template_data))

                EmailTemplate.objects.bulk_create(email_template_objects)
