"""
Global Validation classes.

Common validator classes that we will use on all over our model files.
"""
from django.core.validators import RegexValidator


class phone_validator(RegexValidator):
    """Simple common phone validator."""

    def __init__(self, *args, **kwargs):
        """Override RegexValidator properties."""
        self.regex = "^\+?1?\d{9,15}$"
        self.message = "Phone number must be entered in the \
        format: '+46722222222'. Up to 15 digits allowed."
        self.code = "Phone validator"
        super().__init__(*args, **kwargs)


class name_validator(RegexValidator):
    """Simple common name validator."""

    def __init__(self, *args, **kwargs):
        """Override RegexValidator properties."""
        self.regex = "^[-a-zA-Z0-9.+;,() ]+$"
        self.message = "Name should contain only alphanumeric charactors."
        self.code = "Name validator"
        super().__init__(*args, **kwargs)


def byte_length(s):
    """Calculate byte from given string."""
    return len(s.encode("utf-8"))
