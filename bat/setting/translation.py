"""Model translator file so we can regsiter our models."""
from modeltranslation.translator import TranslationOptions, register

from .models import Category, Status


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    """Add Fields that needed to be translated for category."""

    fields = ("name",)


@register(Status)
class StatusTranslationOptions(TranslationOptions):
    """Add Fields that needed to be translated for status."""

    fields = ("name",)
