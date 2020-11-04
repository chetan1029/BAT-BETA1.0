from collections import OrderedDict
from rolepermissions.roles import RolesManager


def get_list_of_roles_permissions():
    """
    return list of roles available
    """
    all_roles = OrderedDict()
    for role in RolesManager.get_roles():
        role_name = role.get_name()
        print("\nrole_name : ", role_name)
        all_roles[role_name] = {
            "permissions": list(role.permission_names_list()),
        }
    return all_roles


def get_list_of_roles():
    # print("\n all_roles  in se  :", get_list_of_roles_permissions())
    # print("\nroles : ", list(get_list_of_roles_permissions().keys()))
    return list(get_list_of_roles_permissions().keys())


def get_list_of_permissions():
    permissions = []
    for role in RolesManager.get_roles():
        role_name = role.get_name()
        permissions.extend(list(role.permission_names_list()))
    # print("\npermissions : ", permissions)
    return permissions
