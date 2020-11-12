"""File to receive signals from model or actions."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from rolepermissions.roles import assign_role

from bat.company.models import Member

# @receiver(post_save, sender=Member)
# def assign_member_roles(sender, instance, **kwargs):
#     """We will fetch user role from the User and assign after signup."""
#
#     try:
#         if instance.extra_data["user_role"]:
#             assign_role(instance, instance.extra_data["user_role"])
#
#     except (KeyError, TypeError):
#         pass
