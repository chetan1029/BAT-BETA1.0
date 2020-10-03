"""View Classes and functions for main app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.views.generic import TemplateView


class HomePage(TemplateView):
    """Home page."""

    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        """
        Forward loggedin user to dashboard.

        We are using get method because when url called this method called and
        we can access user instance with request and check user is loggedin or
        not.
        """
        if self.request.user.is_authenticated:
            return HttpResponseRedirect("/dashboard/")
        return super().get(request, *args, **kwargs)


class DashboardPage(LoginRequiredMixin, TemplateView):
    """View Class to show dashboard after login."""

    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.now()
        context["language"] = self.request.session.get(
            LANGUAGE_SESSION_KEY, "en"
        )
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "dashboard",
            "menu2": "basic",
        }
        return context


class AmazonDashboardPage(LoginRequiredMixin, TemplateView):
    """View Class to show dashboard after login."""

    template_name = "amazon-dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "amazon",
            "menu1": "amazon-dashboard",
            "menu2": "basic",
        }
        return context


class SupplyChainDashboardPage(LoginRequiredMixin, TemplateView):
    """View Class to show Supply Chain dashboard after login."""

    template_name = "supply-chain-dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "basic",
            "menu2": "dashboard",
        }
        return context


class SalesDashboardPage(LoginRequiredMixin, TemplateView):
    """View Class to show Sales dashboard after login."""

    template_name = "sales-dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "global",
            "menu1": "sales",
            "menu2": "dashboard",
        }
        return context


class AmazonSalesDashboardPage(LoginRequiredMixin, TemplateView):
    """View Class to show Sales dashboard after login."""

    template_name = "amazonsales-dashboard.html"

    def get_context_data(self, **kwargs):
        """Define extra context data that need to pass on template."""
        context = super().get_context_data(**kwargs)
        context["active_menu"] = {
            "dashboard": "amazon",
            "menu1": "sales",
            "menu2": "dashboard",
        }
        return context


class LogoutPage(TemplateView):
    """Template name and url for logout page."""

    template_name = "user/logout.html"
