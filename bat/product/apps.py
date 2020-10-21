from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ProductConfig(AppConfig):
    """Configure setting with the name."""

    name = "bat.product"
    verbose_name = _("Product")

    def ready(self):
        """Can be used as signalling and importing models for that."""
        import bat.product.signals

        pass
