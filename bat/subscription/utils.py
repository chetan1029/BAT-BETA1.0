from django.utils import timezone
from rolepermissions.roles import get_user_roles, RolesManager
from rolepermissions.permissions import revoke_permission, grant_permission
from rolepermissions.checkers import has_permission
from bat.company.models import Company, Member
from bat.subscription.models import Plan, Subscription
from bat.setting.utils import get_status
from bat.subscription.constants import PARENT_SUBSCRIPTION_STATUS, SUBSCRIPTION_STATUS_ACTIVE


def set_subscription_plan_on_company(plan, company):
    """
    subscribe given plan on company
    """
    def _assign_permissions_to_all_members(company, permission_list):
        members = Member.objects.filter(company_id=company.id)
        for member in members:
            roles = get_user_roles(member)
            for role in roles:
                permission_list_for_this_role = permission_list.get(
                    role.get_name(), None)
                for perm in role.permission_names_list():
                    if perm not in permission_list_for_this_role:
                        revoke_permission(member, perm)
                    if perm in permission_list_for_this_role and not has_permission(member, perm):
                        grant_permission(member, perm)

    def _create_subscription(company, plan):
        current = timezone.now()
        data = {}
        data["company"] = company
        data["plan"] = plan
        data["billing_start_date"] = current
        data["billing_end_date"] = current
        data["last_billing_date"] = current
        data["next_billing_date"] = current
        data["status"] = get_status(
            PARENT_SUBSCRIPTION_STATUS, SUBSCRIPTION_STATUS_ACTIVE)
        Subscription.objects.create(**data)

    if isinstance(company, Company) and isinstance(plan, Plan):
        permission_list = plan.permission_list
        _assign_permissions_to_all_members(company, permission_list)
        _create_subscription(company, plan)


def set_default_subscription_plan_on_company(company):
    """
    subscribe default plan on company
    """
    if isinstance(company, Company):
        plan = Plan.objects.filter(default=True).first()
        set_subscription_plan_on_company(plan, company)
