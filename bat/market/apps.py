from django.apps import AppConfig


class MarketConfig(AppConfig):
    name = "bat.market"

    def ready(self):
        try:
            import bat.market.signals
        except ImportError:
            pass
