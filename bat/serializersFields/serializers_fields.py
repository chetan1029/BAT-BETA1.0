from decimal import Decimal

from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Field, ChoiceField, JSONField

from django_countries import countries
from measurement.measures import Weight
from djmoney.money import Money

from bat.company import constants

from bat.globalconstants.constants import CURRENCY_CODE_CHOICES


class WeightField(JSONField):
    def to_representation(self, value):
        '''
        represent weight object to json data
        '''
        ret = {"value": value.value, "unit": value.unit}
        return ret

    def to_internal_value(self, data):
        '''
        generate weight object from json data
        '''
        if not isinstance(data, dict):
            raise ValidationError(
                "%s is not a valid %s" % (data, "format")
            )
        value = data.get("value", None)
        unit = data.get("unit", None)
        if value is None:
            raise ValidationError(
                {"value": _("value is required")})
        try:
            Decimal(value)
        except Exception:
            raise ValidationError(
                {"value": _("value is not a valid decimal")})

        if unit is None:
            raise ValidationError(
                {"unit": _("unit is required")})

        kwargs = {unit: value}
        if unit in constants.WEIGHT_UNIT_TYPE_LIST:
            return Weight(**kwargs)
        else:
            raise ValidationError(
                {"unit": _(f"{unit} is not a valid unit")})


class CountrySerializerField(ChoiceField):
    def __init__(self, **kwargs):
        choices = list(countries)
        super().__init__(choices=choices, **kwargs)

    def to_representation(self, value):
        """
        give code and name of Country.
        """
        if isinstance(value, str):
            return value
        return value.code + " - " + value.name


class TagField(Field):
    def to_representation(self, value):
        """
        Convert from tags to csv string of tag names.
        """
        if not isinstance(value, str):
            value = ",".join(list(value.names()))
        return value

    def to_internal_value(self, data):
        """
        Convert from csv string of tag names to list of tags.
        """
        return data.split(",")


class MoneySerializerField(JSONField):

    def to_representation(self, value):
        '''
        represent money object to json data
        '''
        ret = {"amount": value.amount, "currency": value.currency.code}
        return ret

    def to_internal_value(self, data):
        '''
        generate money object from json data
        '''
        if not isinstance(data, dict):
            raise ValidationError(
                "%s is not a valid %s" % (data, "format")
            )
        amount = data.get("amount", None)
        currency = data.get("currency", None)
        if amount is None:
            raise ValidationError(
                {"amount": _("amount is required")})
        try:
            Decimal(amount)
        except Exception:
            raise ValidationError(
                {"amount": _("amount is not a valid decimal")})

        if currency is None:
            raise ValidationError(
                {"currency": _("currency is required")})

        if currency in CURRENCY_CODE_CHOICES:
            return Money(amount, currency)
        else:
            raise ValidationError(
                {"currency": _(f"{currency} is not a valid currency")})


class QueryFieldsMixin(object):

    # If using Django filters in the API, these labels mustn't conflict with any model field names.
    include_arg_name = 'fields'
    exclude_arg_name = 'fields!'

    # Split field names by this string.  It doesn't necessarily have to be a single character.
    # Avoid RFC 1738 reserved characters i.e. ';', '/', '?', ':', '@', '=' and '&'
    delimiter = ','

    def __init__(self, *args, **kwargs):
        super(QueryFieldsMixin, self).__init__(*args, **kwargs)

        try:
            request = self.context['request']
            method = request.method
        except (AttributeError, TypeError, KeyError):
            # The serializer was not initialized with request context.
            return

        if method != 'GET':
            return

        try:
            query_params = request.query_params
        except AttributeError:
            # DRF 2
            query_params = getattr(request, 'QUERY_PARAMS', request.GET)

        includes = query_params.getlist(self.include_arg_name)
        include_field_names = {name for names in includes for name in names.split(self.delimiter) if name}

        excludes = query_params.getlist(self.exclude_arg_name)
        exclude_field_names = {name for names in excludes for name in names.split(self.delimiter) if name}

        if not include_field_names and not exclude_field_names:
            # No user fields filtering was requested, we have nothing to do here.
            return

        serializer_field_names = set(self.fields)

        fields_to_drop = serializer_field_names & exclude_field_names
        if include_field_names:
            fields_to_drop |= serializer_field_names - include_field_names

        for field in fields_to_drop:
            self.fields.pop(field)