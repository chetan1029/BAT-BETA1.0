from django.apps import AppConfig


class ProductConfig(AppConfig):
    name = "bat.product"

    def ready(self):
        try:
            import bat.product.signals  # noqa F401
        except ImportError:
            pass
