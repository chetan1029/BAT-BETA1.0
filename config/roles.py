"""Roles and Responsibility File."""
from rolepermissions.roles import AbstractUserRole


class CompanyAdmin(AbstractUserRole):
    """Company Admin permissions."""

    available_permissions = {}
