"""Make model available for admin to perform action."""
# https://docs.djangoproject.com/en/3.1/ref/contrib/admin/actions/
from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Category, PaymentTerms, Status


@admin.register(Status)
class StatusAdmin(VersionAdmin):
    """Setup List display, ordering, actions etc."""

    pass


@admin.register(Category)
class CategoryAdmin(VersionAdmin):
    """Setup List display, ordering, actions etc."""

    pass


@admin.register(PaymentTerms)
class PaymentTermsAdmin(VersionAdmin):
    """Setup List display, ordering, actions etc."""

    pass
