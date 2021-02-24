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
            # ext = filename.split(".")[-1]
            # response_args = {'content_type': 'application/'+ext}
            # response = HttpResponse(f, **response_args)
            # response['Content-Disposition'] = 'attachment; filename=' + \
            #     f.name
            # response['Cache-Control'] = 'no-cache'
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


def import_products_bulk_excel(company, import_file):

    data, columns = ProductExcelParser.parse(import_file)
    is_successful, invalid_records = Product.objects.import_bulk(
        data=data, columns=columns, company=company)

    if is_successful:
        if invalid_records:
            error_file = ProductExcelErrorBuilder.write(
                invalid_records, import_file.name)
            if error_file:
                ext = import_file.name.split(".")[-1]
                response_args = {'content_type': 'application/'+ext}
                response = HttpResponse(error_file, **response_args)
                response['Content-Disposition'] = 'attachment; filename=' + \
                    import_file.name
                response['Cache-Control'] = 'no-cache'
            else:
                return HttpResponse({"import performed successfully but can't generate error file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return HttpResponse({"import performed successfully."}, status=status.HTTP_200_OK)
    else:
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def import_products_bulk_csv(company, import_file):

    data, columns = ProductCSVParser.parse(import_file)
    is_successful, invalid_records = Product.objects.import_bulk(
        data=data, columns=columns, company=company)
    if is_successful:
        if invalid_records:
            error_file = ProductCSVErrorBuilder.write(
                invalid_records, import_file.name)
            if error_file:
                ext = import_file.name.split(".")[-1]
                response_args = {'content_type': 'application/'+ext}
                response = HttpResponse(error_file, **response_args)
                response['Content-Disposition'] = 'attachment; filename=' + \
                    import_file.name
                response['Cache-Control'] = 'no-cache'
                return response
            else:
                return HttpResponse({"import performed successfully but can't generate error file."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return HttpResponse({"import performed successfully."}, status=status.HTTP_200_OK)
    else:
        return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
