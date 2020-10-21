"""Midlleware to use for global use mostly related to User settings."""
import logging

from bat.company.models import Member
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class AccountSetupMiddleware(MiddlewareMixin):
    """Force user to setup account."""

    def process_request(self, request):
        """Call is called every new request django make."""
        if request.path != "/company/account-setup":
            try:
                if (
                    request.user.is_authenticated
                    and request.user.extra_data["step_detail"] == "user signup"
                ):
                    return redirect("company:account_setup")
            except TypeError:
                pass


class MemberProfileMiddleware(MiddlewareMixin):
    """Only allow user to access dashbaord as member profile."""

    def process_request(self, request):
        """Call is called every new request django make."""
        if (
            request.user.is_authenticated
            and not request.user.is_superuser
            and request.user.extra_data["step_detail"] != "user signup"
            and (request.path_info != "/accounts/company-login/")
        ):
            try:
                if request.session.get("member_id", False):
                    member_id = request.session.get("member_id")
                    request.member = Member.objects.get(pk=member_id)
                    pass
                else:
                    if request.user.is_memberprofile():
                        return redirect("accounts:company_login")
                    else:
                        pass
            except KeyError:
                return redirect("accounts:company_login")
