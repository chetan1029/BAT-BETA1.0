from rolepermissions.roles import get_user_roles

from bat.company.models import Company, Member
from bat.subscription.models import Plan, Subscription


def set_subscription_plan_on_company(plan, company):
    """
    subscribe given plan on company
    """
    def _assign_permissions_to_all_members(company, permission_list):
        members = Member.objects.filter(company_id=company.id)
        for member in members:
            roles = get_user_roles(member)
            for role in roles:
                permission_list_for_this_role = permission_list.get(role, None)
                pass

    if isinstance(company, Company) and isinstance(plan, Plan):
        permission_list = plan.permission_list
        print("\n\npermission_list :", permission_list,
              "\n\npermission_list type:", type(permission_list))
        _assign_permissions_to_all_members(company, permission_list)


def set_default_subscription_plan_on_company(company):
    """
    subscribe default plan on company
    """
    if isinstance(company, Company):
        plan = Plan.objects.filter(default=True).first()
        set_subscription_plan_on_company(plan, company)
