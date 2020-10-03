"""Midlleware to use for global use mostly related to User settings."""
import logging

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class AccountSetupMiddleware(MiddlewareMixin):
    """Force user to setup account."""

    def process_request(self, request):
        """Call is called every new request django make."""
        logger = logging.getLogger(__name__)
        logger.warning("---Calling Account Setup---")
        if (
            request.user.is_authenticated
            and request.user.extra_data["step_detail"] == "user signup"
        ):
            logger.warning("---Calling Inside---")
            return redirect("company:account_setup")
