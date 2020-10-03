"""Django config for application."""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CompanyConfig(AppConfig):
    """Configure setting with the name."""

    name = "bat.company"
    verbose_name = _("Company")

    def ready(self):
        """Can be used as signalling and importing models for that."""
        pass
