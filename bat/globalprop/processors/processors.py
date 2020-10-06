"""
Global Processors.

If we need to declear something on global. We can use proccessors and
add them in setting file TEMPLATES -> context_processors option to make them
global.
"""
from bat.company.models import Member
from bat.setting.models import Category
from django.utils.translation import ugettext_lazy as _


def vendor_categories(request):
    """Fetch all the Vendor Categories."""
    return {
        "vendor_categories": Category.objects.filter(
            parent__name__exact=_("Vendors")
        )
    }


def saleschannels(request):
    """Fetch all the Sales Channel type."""
    return {
        "saleschannels": Category.objects.filter(
            parent__name__exact=_("Sales Channel")
        )
    }


def member(request):
    """Fetch all the Sales Channel type."""
    try:
        if request.user.is_authenticated and request.session.get("member_id"):
            member_id = request.session.get("member_id")
            return {"member": Member.objects.get(pk=member_id)}
        else:
            return ""
    except KeyError:
        return ""
