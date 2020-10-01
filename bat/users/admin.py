"""Manage following models from Admin."""

from bat.users.models import User
from django.contrib import admin
from reversion.admin import VersionAdmin
from rolepermissions.admin import RolePermissionsUserAdminMixin


class UserAdmin(RolePermissionsUserAdminMixin, VersionAdmin):
    """Setup User."""

    pass


admin.site.register(User, UserAdmin)
