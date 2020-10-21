"""
Global Processors.

If we need to declear something on global. We can use proccessors and
add them in setting file TEMPLATES -> context_processors option to make them
global.
"""
from bat.company.models import Member
from bat.setting.models import Category
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
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


def loggedin_member(request):
    """Fetch all the Sales Channel type."""
    try:
        if request.user.is_authenticated and request.session.get("member_id"):
            try:
                member_id = request.session.get("member_id")
                return {"loggedin_member": Member.objects.get(pk=member_id)}
            except ObjectDoesNotExist:
                logout(request)
                return HttpResponseRedirect(reverse("accounts:login"))
        else:
            return ""
    except KeyError:
        return ""
