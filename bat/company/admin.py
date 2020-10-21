"""Make model available for admin to perform action."""
# https://docs.djangoproject.com/en/3.1/ref/contrib/admin/actions/
from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Company, CompanyType, Member


@admin.register(Company)
class CompanyAdmin(VersionAdmin):
    """Setup List display, ordering, actions etc."""

    pass


@admin.register(Member)
class MemberAdmin(VersionAdmin):
    """Setup List display, ordering, actions etc."""

    pass


@admin.register(CompanyType)
class CompanyTypeAdmin(VersionAdmin):
    """Setup List display, ordering, actions etc."""

    pass
