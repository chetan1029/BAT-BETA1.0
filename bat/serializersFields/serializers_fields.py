from decimal import Decimal

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Field, ChoiceField

from django_countries import countries
from measurement.measures import Weight

from bat.company import constants


class WeightField(Field):
    def to_representation(self, value):
        ret = {"weight": value.value, "unit": value.unit}
        return ret

    def to_internal_value(self, data):
        try:
            if not isinstance(data, dict):
                raise Exception
            # data = eval(data)
            unit = data["unit"]
            value = data["weight"]
            kwargs = {unit: value}
            if unit in constants.WEIGHT_UNIT_TYPE_LIST:
                return Weight(**kwargs)
            else:
                raise ValidationError("%s is not a valid %s" % (data, "Unit"))
        except Exception:
            if data:
                raise ValidationError(
                    "%s is not a valid %s" % (data, "format")
                )
            else:
                if self.required:
                    raise ValidationError("%s is %s" % ("weight", "required"))
                else:
                    # TODO
                    return data


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