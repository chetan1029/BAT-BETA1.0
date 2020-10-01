"""Custom made Utils file to create some useful functions."""
import pytz

from django.utils import timezone


def make_utc(dt):
    """Convert local datetime to UTC."""
    if dt.is_naive():
        dt = timezone.make_aware(dt)
    return dt.astimezone(pytz.utc)
