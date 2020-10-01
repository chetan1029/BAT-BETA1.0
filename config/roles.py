"""Roles and Responsibility File."""
from rolepermissions.roles import AbstractUserRole


class SupplyChainManager(AbstractUserRole):
    """Supply chain manager permissions."""

    available_permissions = {
        "view_supply_chain_dashboard": True,
        "edit_supply_chain_dashboard": True,
        "view_product_catalog": True,
        "add_product": True,
        "edit_product": True,
        "delete_product": True,
        "view_vendor": True,
        "add_vendor": True,
        "edit_vendor": True,
        "delete_vendor": True,
        "view_payment_terms": True,
        "add_payment_terms": True,
        "delete_payment_terms": True,
        "view_certification": True,
        "add_certification": True,
        "delete_certification": True,
        "view_vendor_contacts": True,
        "add_vendor_contacts": True,
        "edit_vendor_contacts": True,
        "delete_vendor_contacts": True,
        "view_vendor_bank_info": True,
        "add_vendor_bank_info": True,
        "delete_vendor_bank_info": True,
        "view_vendor_contract": True,
        "add_vendor_contract": True,
        "delete_vendor_contract": True,
        "view_vendor_price_list": True,
        "add_vendor_price_list": True,
        "view_vendor_mold": True,
        "add_vendor_mold": True,
        "delete_vendor_mold": True,
        "view_me": True,
        "add_me": True,
        "delete_me": True,
        "view_order": True,
        "edit_order": True,
        "delete_order": True,
        "generate_order": True,
        "confirm_po": True,
        "upload_pi": True,
        "close_order": True,
        "view_order_payment": True,
        "add_order_payment": True,
        "edit_order_payment": True,
        "delete_order_payment": True,
        "view_shipment": True,
        "add_shipment": True,
        "edit_shipment": True,
        "delete_shipment": True,
    }


class SalesManager(AbstractUserRole):
    """Sales manager permissions."""

    available_permissions = {"sales": True, "payments": True}


class InventoryManager(AbstractUserRole):
    """Inventory Manager permissions."""

    available_permissions = {"inventorize": True}


class PpcManager(AbstractUserRole):
    """PPC Manager permissions."""

    available_permissions = {"ppc": True}


class OptimisationManager(AbstractUserRole):
    """Optimisation Manager permissions."""

    available_permissions = {
        "view_optimisation_dashboard": True,
        "edit_optimisation_dashboard": True,
        "view_clr_catalog": True,
        "view_optimisation": True,
        "upload_clr_catalog": True,
        "copy_optimisation": True,
        "clone_optimisation": True,
        "edit_optimisation": True,
        "delete_optimisation": True,
        "share_optimisation": True,
        "submit_to_amazon": True,
        "manage_clr_reports": True,
        "my_contributions": True,
    }


class SettingControl(AbstractUserRole):
    """Website setting permissions."""

    available_permissions = {
        "category_management": True,
        "status_management": True,
        "catalog_management": True,
        "vat_management": True,
        "company_setting": True,
        "currency_management": True,
    }


class UserRoleControl(AbstractUserRole):
    """Control roles and permissions for users."""

    available_permissions = {
        "view_roles": True,
        "edit_roles": True,
        "delete_roles": True,
    }


class ThirdPartyOptimisation(AbstractUserRole):
    """3rd Party Optimisation Manager permissions."""

    available_permissions = {
        "edit_optimisation": True,
        "view_optimisation": True,
        "my_contributions": True,
    }
