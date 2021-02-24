import tempfile
import csv
from io import StringIO

from django.http import HttpResponse

from rest_framework import status

import openpyxl
from bat.product.models import Product


class ProductCSVErrorBuilder(object):

    @classmethod
    def write(cls, invalid_records, filename):

        # header mapping
        headers = [*invalid_records[0]]
        try:
            # create csv file
            csvfile = StringIO()
            dict_writer = csv.DictWriter(csvfile, headers, extrasaction='ignore')
            dict_writer.writeheader()
            dict_writer.writerows(invalid_records)
            csvfile.seek(0)
            return csvfile
        except Exception:
            return None


class ProductCSVParser(object):

    @classmethod
    def parse(cls, csv_file):
        data = []
        # read file
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file, delimiter=',')
        for row in reader:
            row.pop("id")
            data.append(row)
        header = reader.fieldnames
        header.remove("id")
        return data, header


class ProductExcelErrorBuilder(object):

    @classmethod
    def write(cls, invalid_records, filename):
        # Temporary files
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_xlsx_file_path = tmp_dir.name + "/" + filename

        # create Workbook
        wb = openpyxl.Workbook()
        ws = wb.active

        # header mapping
        headers = [*invalid_records[0]]
        ws.append(headers)

        try:
            # write data
            for row in invalid_records:
                ws.append(list(row.values()))
            wb.save(tmp_xlsx_file_path)
            wb.close()

            f = open(tmp_xlsx_file_path, "rb")
            return f
        except Exception:
            return None


class ProductExcelParser(object):

    @classmethod
    def parse(cls, excel_file):
        data = []
        # read file
        ws = openpyxl.load_workbook(excel_file)
        sheet = ws.active

        # get column's list
        header = [cell.value for cell in sheet[1]]
        header.remove("id")

        for row in sheet.iter_rows(min_row=2, min_col=2):
            values = {}
            # process each value
            for key, cell in zip(header, row):
                values[key] = cell.value
            data.append(values)
        return data, header
