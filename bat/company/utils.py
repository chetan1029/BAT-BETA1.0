from collections import OrderedDict

from django.shortcuts import get_object_or_404
from rolepermissions.roles import RolesManager

from bat.company.models import Member, Company, CompanyPaymentTerms
from bat.setting.models import PaymentTerms


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
