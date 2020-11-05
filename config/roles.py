"""Roles and Responsibility File."""
from rolepermissions.roles import AbstractUserRole


class CompanyAdmin(AbstractUserRole):
    """Company Admin permissions."""

    available_permissions = {
        "update_company_profile": True,
        "view_staff_member": True,
        "add_staff_member": True,
        "change_staff_member": True,
        "delete_staff_member": True,
        "view_payment_terms": True,
        "add_payment_terms": True,
        "change_payment_terms": True,
        "delete_payment_terms": True,
        "view_membership_plan": True,
        "add_membership_plan": True,
        "change_membership_plan": True,
        "delete_membership_plan": True,
        "view_company_banks": True,
        "add_company_banks": True,
        "change_company_banks": True,
        "delete_company_banks": True,
        "view_company_locations": True,
        "add_company_locations": True,
        "change_company_locations": True,
        "delete_company_locations": True,
        "view_packing_box": True,
        "add_packing_box": True,
        "change_packing_box": True,
        "delete_packing_box": True,
        "view_taxes": True,
        "add_taxes": True,
        "change_taxes": True,
        "delete_taxes": True,
        "view_hscode": True,
        "add_hscode": True,
        "change_hscode": True,
        "delete_hscode": True,
        "view_product": True,
        "add_product": True,
        "change_product": True,
        "delete_product": True,
    }


class SupplyChainManager(AbstractUserRole):
    """Supply Chain Manager permissions."""

    available_permissions = {
        "view_staff_member": True,
        "add_staff_member": True,
        "change_staff_member": True,
        "archived_staff_member": False,
        "view_payment_terms": True,
        "add_payment_terms": True,
        "change_payment_terms": True,
        "archive_payment_terms": True,
        "restore_payment_terms": True,
        "view_membership_plan": True,
        "add_membership_plan": True,
        "change_membership_plan": True,
        "view_company_banks": True,
        "add_company_banks": True,
        "change_company_banks": True,
        "archived_company_banks": True,
        "view_company_locations": True,
        "add_company_locations": True,
        "change_company_locations": True,
        "archived_company_locations": True,
        "view_packing_box": True,
        "add_packing_box": True,
        "change_packing_box": True,
        "archived_packing_box": True,
        "view_taxes": True,
        "add_taxes": True,
        "change_taxes": True,
        "archived_taxes": True,
        "view_hscode": True,
        "add_hscode": True,
        "change_hscode": True,
        "archived_hscode": True,
        "view_product": True,
        "add_product": True,
        "change_product": True,
        "archived_product": True,
    }


class VendorAdmin(AbstractUserRole):
    """
    Vendor Admin permissions.

    He just has access of vendors access functions.
    """

    available_permissions = {
        "update_company_profile": True,
        "view_staff_member": True,
        "add_staff_member": True,
        "change_staff_member": True,
        "delete_staff_member": True,
    }
