import os
from django import forms
from crispy_forms.layout import Field, MultiWidgetField
from django.core.exceptions import ValidationError

class CustomCheckbox(Field):
    template = 'forms/custom_checkbox.html'


class CustomCheckboxSelectMultiple(Field):
    template = 'forms/custom_checkboxselectmultiple.html'

class CsvFileField(forms.FileField):
    def validate(self, value):
        # First run the parent class' validation routine
        super().validate(value)
        # Run our own file extension check
        file_extension = os.path.splitext(value.name)[1]
        if file_extension != '.csv':
            raise ValidationError(
                 ('Invalid file is provided. Please provide a csv file'),
                 code='invalid'
            )