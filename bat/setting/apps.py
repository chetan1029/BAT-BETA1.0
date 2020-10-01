"""Django config for application."""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SettingConfig(AppConfig):
    """Configure setting with the name."""

    name = "bat.setting"
    verbose_name = _("Setting")

    def ready(self):
        """Can be used as signalling and importing models for that."""
        import bat.setting.signals

        pass
