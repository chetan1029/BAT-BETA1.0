"""
Global Processors.

If we need to declear something on global. We can use proccessors and
add them in setting file TEMPLATES -> context_processors option to make them
global.
"""
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
