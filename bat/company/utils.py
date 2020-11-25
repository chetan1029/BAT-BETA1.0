from collections import OrderedDict
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rolepermissions.checkers import has_permission
from rolepermissions.roles import RolesManager

from bat.company.models import Member


def get_member(company_id=None, user_id=None):
    """
    get member based on company and user
    """
    member = get_object_or_404(Member, company__id=company_id, user=user_id)
    return member


def get_list_of_roles_permissions():
    """
    return list of roles available
    """
    all_roles = OrderedDict()
    for role in RolesManager.get_roles():
        role_name = role.get_name()

        all_roles[role_name] = {
            "permissions": list(role.permission_names_list())
        }
    return all_roles


def get_list_of_roles():

    return list(get_list_of_roles_permissions().keys())


def get_list_of_permissions():
    permissions = []
    for role in RolesManager.get_roles():
        permissions.extend(list(role.permission_names_list()))
    return permissions
