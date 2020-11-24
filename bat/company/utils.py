from collections import OrderedDict
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rolepermissions.checkers import has_permission
from rolepermissions.roles import RolesManager

from bat.company.models import Member
from bat.setting.models import Category


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
        role_name = role.get_name()
        permissions.extend(list(role.permission_names_list()))
    return permissions


def has_permissions(object=None, permissions=[]):
    """
    docstring
    """
    for perm in permissions:
        if not has_permission(object, perm):
            return False
    return True


def get_cbm(length, width, depth, unit):
    """Convert measurement into CBM."""
    if length and width and depth and unit:
        cbm = Decimal(0.0)
        if unit == "cm":
            cbm = round(
                (
                    (Decimal(length) * Decimal(width) * Decimal(depth))
                    / 1000000
                ),
                2,
            )
        elif unit == "in":
            cbm = round(
                (
                    (
                        Decimal(length)
                        * Decimal(2.54)
                        * Decimal(width)
                        * Decimal(2.54)
                        * Decimal(depth)
                        * Decimal(2.54)
                    )
                    / 1000000
                ),
                2,
            )

        elif unit == "m":
            cbm = round(
                (

                    Decimal(length)
                    * Decimal(width)
                    * Decimal(depth)

                ),
                2,
            )
        return cbm


# def test():
#     """
#     docstring
#     """
#     data = {"id": 1, "name": "test"}
#     choices = list(Category.objects.values("id", "name"))
#     if data in choices:
#         print("\n\n YES \n\n")
#     else:
#         print("\n\n NO \n\n")
