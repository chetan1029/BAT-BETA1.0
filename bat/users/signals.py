"""File to receive signals from model or actions."""
import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from invitations.utils import get_invitation_model

from notifications.signals import notify

from rolepermissions.permissions import revoke_permission
from rolepermissions.roles import RolesManager, assign_role

from bat.company.models import Company, CompanyType, Member
from bat.users.models import InvitationDetail


logger = logging.getLogger(__name__)
Invitation = get_invitation_model()
User = get_user_model()


@receiver(post_save, sender=User)
def process_invitations(sender, instance, **kwargs):
    """We will fetch all the invitations for user after signup."""
    invitations = Invitation.objects.filter(
        email=instance.email, accepted=True
    )
    if invitations.exists():
        for invitation in invitations:
            user_detail = invitation.user_detail
            job_title = user_detail["job_title"]
            company_detail = invitation.company_detail
            company_id = company_detail["company_id"]
            user_roles = invitation.user_roles
            role = user_roles["role"]

            perms = user_roles["perms"]

            if invitation.extra_data["type"] == "Vendor Invitation":
                vendor_name = company_detail["vendor_name"]
                vendor_type = company_detail["vendor_type"]
                vendor = Company(name=vendor_name, email=invitation.email)
                vendor.save()
                companytype = CompanyType(
                    partner=vendor,
                    company_id=company_id,
                    category_id=vendor_type,
                )
                companytype.save()

                member, _c = Member.objects.get_or_create(
                    job_title=job_title,
                    user=instance,
                    company=vendor,
                    invited_by=invitation.inviter,
                    is_admin=True,
                    is_active=True,
                    invitation_accepted=True,
                )
            else:
                member, _c = Member.objects.get_or_create(
                    job_title=job_title,
                    user=instance,
                    company_id=company_id,
                    invited_by=invitation.inviter,
                    is_admin=False,
                    is_active=True,
                    invitation_accepted=True,
                )

            assign_role(member, role)
            role_obj = RolesManager.retrieve_role(role)
            # remove unneccesary permissions
            for perm in role_obj.permission_names_list():
                if perm not in perms:
                    revoke_permission(member, perm)

            notify.send(
                instance,
                recipient=invitation.inviter,
                verb=_("Accepted your invitation"),
                target=member.company,
            )

            invitation.delete()
