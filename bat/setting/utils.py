"""Utility function for setting modules."""

from bat.setting.models import Status
from django.contrib.auth import get_user_model

User = get_user_model()


def get_status(parent_status_name, status_name=""):
    """Get or Create a new status."""
    superusers = User.objects.filter(is_superuser=True).first()
    parent_status, create = Status.objects.get_or_create(
        name=parent_status_name, defaults={"user": superusers}
    )
    if status_name:
        status, create = Status.objects.get_or_create(
            name=status_name,
            parent=parent_status,
            defaults={"user": superusers},
        )
        return status
    else:
        return parent_status
