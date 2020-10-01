"""Django config for application."""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CoreConfig(AppConfig):
    """Configure setting with the name."""

    name = "bat.core"
    verbose_name = _("Core")

    def ready(self):
        """Can be used as signalling and importing models for that."""
        pass
