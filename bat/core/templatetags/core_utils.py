import datetime
import json
from decimal import Decimal

import pytz
from dateutil.parser import parse

from django import template
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

register = template.Library()


@register.filter
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


@register.filter
def is_date(s):
    try:
        parse(s)
        return True
    except ValueError:
        return False


@register.filter
def formattedFieldChanges(changes):
    try:
        repr = ""
        for field, vals in json.loads(changes).items():
            if not field == "update_date":
                if is_number(vals[0]) and is_number(vals[1]):
                    if Decimal(vals[0]) != Decimal(vals[1]):
                        from_value = str(vals[0])
                        to_value = str(vals[1])
                        repr += (
                            field
                            + " from "
                            + from_value
                            + " to "
                            + to_value
                            + ", "
                        )
                elif is_date(vals[0]) and is_date(vals[1]):
                    if parse(vals[0]).strftime("%d %B %Y") != parse(
                        vals[1]
                    ).strftime("%d %B %Y"):
                        from_value = str(parse(vals[0]).strftime("%d %B %Y"))
                        to_value = str(parse(vals[1]).strftime("%d %B %Y"))
                        repr += (
                            field
                            + " from "
                            + from_value
                            + " to "
                            + to_value
                            + ", "
                        )
                else:
                    from_value = str(vals[0])
                    to_value = str(vals[1])
                    if from_value == "None":
                        from_value = "--"
                    if to_value == "None":
                        to_value = "--"
                    if from_value != to_value:
                        repr += (
                            field
                            + " from "
                            + from_value
                            + " to "
                            + to_value
                            + ", "
                        )
        return repr[:-2]
    except Exception as e:
        print(e)
        return ""


@register.simple_tag
def time_of_day():
    """Get greeting for the day."""
    cur_time = datetime.datetime.now(
        tz=pytz.timezone(str(timezone.get_current_timezone()))
    )
    if cur_time.hour < 12:
        return _("Good Morning")
    elif 12 <= cur_time.hour < 18:
        return _("Good Afternoon")
    else:
        return _("Good Evening")


@register.simple_tag
def snake_to_title(s):
    """Change a Snake format text to title."""
    return " ".join(x.capitalize() for x in s.split("_"))
