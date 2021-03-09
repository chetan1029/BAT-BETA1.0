import os
import tempfile

from decimal import Decimal
from weasyprint import HTML
from rolepermissions.checkers import has_permission

from django.core.files import File
from django.template.loader import render_to_string

from bat.product.constants import PRODUCT_STATUS_DRAFT, PRODUCT_PARENT_STATUS
from bat.setting.utils import get_status


def has_any_permission(obj, permission_list):
    """
    docstring
    """
    for perm in permission_list:
        if has_permission(obj, perm):
            return True
    return False


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


def get_status_object(data, status_field="status"):
    if not data.get(status_field, None):
        return get_status(
            PRODUCT_PARENT_STATUS, PRODUCT_STATUS_DRAFT)
    else:
        status_name = data.get(status_field, None)
        return get_status("Basic", status_name)
