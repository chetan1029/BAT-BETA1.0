"""Django config for application."""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UsersConfig(AppConfig):
    """Configure setting with the name."""

    name = "bat.users"
    verbose_name = _("Users")

    def ready(self):
        """Can be used as signalling and importing models for that."""
        import bat.users.signals

        pass
