import os
import tempfile

from decimal import Decimal
from weasyprint import HTML

from django.core.files import File
from django.template.loader import render_to_string


def set_field_errors(list_of_errors, field, error_msg):
    errors = list_of_errors.copy()
    if field in list_of_errors:
        errors[field].append(error_msg)
    else:
        errors[field] = [error_msg]
    return errors


def get_cbm(length, width, depth, unit):
    """Convert measurement into CBM."""
    if length and width and depth and unit:
        cbm = Decimal(0.0)
        if unit == "cm":
            cbm = round(
                (
                    (Decimal(length) * Decimal(width) * Decimal(depth))
                    / 1000000
                ),
                2,
            )
        elif unit == "in":
            cbm = round(
                (
                    (
                        Decimal(length)
                        * Decimal(2.54)
                        * Decimal(width)
                        * Decimal(2.54)
                        * Decimal(depth)
                        * Decimal(2.54)
                    )
                    / 1000000
                ),
                2,
            )

        elif unit == "m":
            cbm = round(
                (

                    Decimal(length)
                    * Decimal(width)
                    * Decimal(depth)

                ),
                2,
            )
        return cbm


def pdf_file_from_html(data, template_path, file_name):
    """
    generate pdf file from html template with given context data
    """

    tmp_dir = tempfile.TemporaryDirectory()
    tmp_file_path = tmp_dir.name + file_name + ".pdf"
    path = "pdf-templates/"
    html_template = render_to_string(
        path + template_path,
        data,
    )
    pdf_file = HTML(
        string=html_template
    ).write_pdf(
        tmp_file_path
    )
    f = open(tmp_file_path, "rb")
    final_file = File(f)
    return final_file
