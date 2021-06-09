from django.apps import AppConfig


class AutoemailConfig(AppConfig):
    name = "bat.autoemail"

    def ready(self):
        try:
            import bat.autoemail.signals 
        except ImportError:
            pass
