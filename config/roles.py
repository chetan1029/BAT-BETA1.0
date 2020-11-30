"""Roles and Responsibility File."""
from rolepermissions.roles import AbstractUserRole


class CompanyAdmin(AbstractUserRole):
    """Company Admin permissions."""

    available_permissions = {
        # company profile
        "update_company_profile": True,
        # Staff member
        "view_staff_member": True,
        "add_staff_member": True,
        "change_staff_member": True,
        "archived_staff_member": True,
        "restore_staff_member": True,
        "delete_staff_member": True,
        # Payment terms
        "view_payment_terms": True,
        "add_payment_terms": True,
        "change_payment_terms": True,
        "archived_payment_terms": True,
        "restore_payment_terms": True,
        "delete_payment_terms": True,
        # Membership Plan
        "view_membership_plan": True,
        "add_membership_plan": True,
        "change_membership_plan": True,
        "delete_membership_plan": True,
        # Company bank
        "view_company_banks": True,
        "add_company_banks": True,
        "change_company_banks": True,
        "archived_company_banks": True,
        "restore_company_banks": True,
        "delete_company_banks": True,
        # Company Location
        "view_company_locations": True,
        "add_company_locations": True,
        "change_company_locations": True,
        "archived_company_locations": True,
        "restore_company_locations": True,
        "delete_company_locations": True,
        # Company Packing Box
        "view_packing_box": True,
        "add_packing_box": True,
        "change_packing_box": True,
        "archived_packing_box": True,
        "restore_packing_box": True,
        "delete_packing_box": True,
        # Company Tax
        "view_taxes": True,
        "add_taxes": True,
        "change_taxes": True,
        "archived_taxes": True,
        "restore_taxes": True,
        "delete_taxes": True,
        # Company HSCode
        "view_hscode": True,
        "add_hscode": True,
        "change_hscode": True,
        "archived_hscode": True,
        "restore_hscode": True,
        "delete_hscode": True,
        # Product
        "view_product": True,
        "add_product": True,
        "active_product": True,
        "change_product": True,
        "archived_product": True,
        "restore_product": True,
        "delete_product": True,
        # Company Contract
        "view_company_contract": True,
        "add_company_contract": True,
        "approve_company_contract": True,
        "change_company_contract": True,
        "archived_company_contract": True,
        "restore_company_contract": True,
        "delete_company_contract": True,
        # Company Credential
        "view_company_credential": True,
        "add_company_credential": True,
        "change_company_credential": True,
        "archived_company_credential": True,
        "restore_company_credential": True,
        "delete_company_credential": True,
        # Component ME
        "view_component_me": True,
        "add_component_me": True,
        "approve_component_me": True,
        "change_component_me": True,
        "archived_component_me": True,
        "restore_component_me": True,
        "delete_component_me": True,
        # Component Golden Sample
        "view_component_golden_sample": True,
        "add_component_golden_sample": True,
        "approve_component_golden_sample": True,
        "change_component_golden_sample": True,
        "archived_component_golden_sample": True,
        "restore_component_golden_sample": True,
        "delete_component_golden_sample": True,
        # Component Price
        "view_component_price": True,
        "add_component_price": True,
        "approve_component_price": True,
        "change_component_price": True,
        "archived_component_price": True,
        "restore_component_price": True,
        "delete_component_price": True,
        # Company Order
        "view_order": True,
        "add_order": True,
        "approve_order": True,
        "change_order": True,
        "archived_order": True,
        "restore_order": True,
        "delete_order": True,
        # Company Order Delivery
        "view_order_delivery": True,
        "add_order_delivery": True,
        "approve_order_delivery": True,
        "change_order_delivery": True,
        "archived_order_delivery": True,
        "restore_order_delivery": True,
        "delete_order_delivery": True,
        # Company Order Delivery Test Report and Company Orde Inspection
        "view_order_inspection": True,
        "add_order_inspection": True,
        "approve_order_inspection": True,
        "change_order_inspection": True,
        "archived_order_inspection": True,
        "restore_order_inspection": True,
        "delete_order_inspection": True,
        # Company Order Case
        "view_order_case": True,
        "add_order_case": True,
        "approve_order_case": True,
        "change_order_case": True,
        "archived_order_case": True,
        "restore_order_case": True,
        "delete_order_case": True,
        # Company Order Payment
        "view_order_payment": True,
        "add_order_payment": True,
        "approve_order_payment": True,
        "change_order_payment": True,
        "archived_order_payment": True,
        "restore_order_payment": True,
        "delete_order_payment": True,
    }


class SupplyChainManager(AbstractUserRole):
    """Supply Chain Manager permissions."""

    available_permissions = {
        # Staff member
        "view_staff_member": True,
        "add_staff_member": True,
        "change_staff_member": True,
        "archived_staff_member": False,
        "restore_staff_member": False,
        "delete_staff_member": False,
        # Payment Terms
        "view_payment_terms": True,
        "add_payment_terms": True,
        "change_payment_terms": True,
        "archived_payment_terms": True,
        "restore_payment_terms": True,
        "delete_payment_terms": False,
        # Membership Plan
        "view_membership_plan": True,
        "add_membership_plan": True,
        "change_membership_plan": True,
        "delete_membership_plan": False,
        # Company Bank
        "view_company_banks": True,
        "add_company_banks": True,
        "change_company_banks": True,
        "archived_company_banks": True,
        "restore_company_banks": True,
        "delete_company_banks": False,
        # Company Location
        "view_company_locations": True,
        "add_company_locations": True,
        "change_company_locations": True,
        "archived_company_locations": True,
        "restore_company_locations": True,
        "delete_company_locations": False,
        # Company Packing Box
        "view_packing_box": True,
        "add_packing_box": True,
        "change_packing_box": True,
        "archived_packing_box": True,
        "restore_packing_box": True,
        "delete_packing_box": False,
        # Company Tax
        "view_taxes": True,
        "add_taxes": True,
        "change_taxes": True,
        "archived_taxes": True,
        "restore_taxes": True,
        "delete_taxes": False,
        # Company HSCode
        "view_hscode": True,
        "add_hscode": True,
        "change_hscode": True,
        "archived_hscode": True,
        "restore_hscode": True,
        "delete_hscode": False,
        # Product
        "view_product": True,
        "add_product": True,
        "active_product": False,
        "change_product": True,
        "archived_product": True,
        "restore_product": True,
        "delete_product": False,
        # Company Contract
        "view_company_contract": True,
        "add_company_contract": True,
        "approve_company_contract": False,
        "change_company_contract": True,
        "archived_company_contract": True,
        "restore_company_contract": True,
        "delete_company_contract": False,
        # Company Credential
        "view_company_credential": True,
        "add_company_credential": True,
        "change_company_credential": True,
        "archived_company_credential": True,
        "restore_company_credential": True,
        "delete_company_credential": True,
        # Component ME
        "view_component_me": True,
        "add_component_me": True,
        "approve_component_me": False,
        "change_component_me": True,
        "archived_component_me": True,
        "restore_component_me": True,
        "delete_component_me": False,
        # Component Golden Sample
        "view_component_golden_sample": True,
        "add_component_golden_sample": True,
        "approve_component_golden_sample": False,
        "change_component_golden_sample": True,
        "archived_component_golden_sample": True,
        "restore_component_golden_sample": True,
        "delete_component_golden_sample": False,
        # Component Price
        "view_component_price": True,
        "add_component_price": True,
        "approve_component_price": False,
        "change_component_price": True,
        "archived_component_price": True,
        "restore_component_price": True,
        "delete_component_price": False,
        # Company Order
        "view_order": True,
        "add_order": True,
        "approve_order": False,
        "change_order": True,
        "archived_order": True,
        "restore_order": True,
        "delete_order": False,
        # Company Order Delivery
        "view_order_delivery": True,
        "add_order_delivery": True,
        "approve_order_delivery": False,
        "change_order_delivery": True,
        "archived_order_delivery": True,
        "restore_order_delivery": True,
        "delete_order_delivery": False,
        # Company Order Delivery Test Report and Company Orde Inspection
        "view_order_inspection": True,
        "add_order_inspection": True,
        "approve_order_inspection": False,
        "change_order_inspection": True,
        "archived_order_inspection": True,
        "restore_order_inspection": True,
        "delete_order_inspection": False,
        # Company Order Case
        "view_order_case": True,
        "add_order_case": True,
        "approve_order_case": False,
        "change_order_case": True,
        "archived_order_case": True,
        "restore_order_case": True,
        "delete_order_case": False,
        # Company Order Payment
        "view_order_payment": True,
        "add_order_payment": True,
        "approve_order_payment": False,
        "change_order_payment": True,
        "archived_order_payment": True,
        "restore_order_payment": True,
        "delete_order_payment": False,
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
