"""Midlleware to use for global use mostly related to settins."""
import logging

import pytz

from django.utils import timezone


class TimezoneMiddleware:
    """Set user selected timezone."""

    def __init__(self, get_response):
        """Inti function called when server start."""
        self.get_response = get_response

    def __call__(self, request):
        """Call is called every new request django make."""
        logger = logging.getLogger(__name__)
        logger.warning("---TimeZone Setup---")
        tzname = request.session.get("user_timezone")
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)
