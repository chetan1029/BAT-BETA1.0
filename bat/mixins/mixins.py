import datetime
import tempfile
import djqscsv
import json
from openpyxl import Workbook

from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.utils.text import slugify

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class ArchiveMixin:
    @action(detail=True, methods=["post"])
    def archive(self, request, *args, **kwargs):
        """Set the archive action."""
        instance = self.get_object()

        if not instance.is_active:
            return Response({"detail": _("Already archived")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                instance.archive()
            return Response({"detail": self.archive_message}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response({"detail": _("Can't archive")}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class RestoreMixin:
    @action(detail=True, methods=["post"])
    def restore(self, request, *args, **kwargs):
        """Set the restore action."""
        instance = self.get_object()
        if instance.is_active:
            return Response({"detail": _("Already active")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                instance.restore()
            return Response({"detail": self.restore_message}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response({"detail": _("Can't restore")}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ExportMixin:

    @action(detail=False, methods=["get"])
    def csvexport(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset())
        if getattr(self, "export_fields", None):
            queryset = queryset.values(*self.export_fields)

        if getattr(self, "field_header_map", None):
            return djqscsv.render_to_csv_response(
                queryset, append_datestamp=True, field_header_map=self.field_header_map)
        else:
            return djqscsv.render_to_csv_response(
                queryset, append_datestamp=True)

    @action(detail=False, methods=["get"])
    def xlsxeport(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset())
        if getattr(self, "export_fields", None):
            queryset = queryset.values(*self.export_fields)

        # get filenames
        formatted_datestring = datetime.date.today().strftime("%Y%m%d")
        filename_xlsx = slugify(queryset.model.__name__) + \
            "_" + formatted_datestring + '_export.xlsx'

        # Temporary files
        tmp_dir = tempfile.TemporaryDirectory()
        tmp_xlsx_file_path = tmp_dir.name + "/" + filename_xlsx

        # create Workbook
        wb = Workbook()
        ws = wb.active

        # header mapping
        if type(queryset).__name__ == 'ValuesQuerySet':
            values_qs = queryset
        else:
            # could be a non-values qs, or could be django 1.9+
            iterable_class = getattr(queryset, '_iterable_class', object)
            if iterable_class.__name__ == 'ValuesIterable':
                values_qs = queryset
            else:
                values_qs = queryset.values()
        qs_header = list(values_qs.query.values_select)
        header_map = getattr(self, "field_header_map", None)
        if header_map:
            header = qs_header.copy()
            for key, value in header_map.items():
                header[header.index(key)] = value
            ws.append(header)
        else:
            ws.append(qs_header)

        try:
            # write data
            if queryset.exists():
                if not isinstance(queryset.first(), dict):
                    queryset = queryset.values(*qs_header)
                for row in queryset:
                    row2 = []
                    for key, value in row.items():
                        if isinstance(value, dict):
                            value = json.dumps(value)
                        row2.append(value)
                    ws.append(row2)
            wb.save(tmp_xlsx_file_path)
            wb.close()

            # response
            f = open(tmp_xlsx_file_path, "rb")

            response_args = {'content_type': 'application/xlsx'}
            response = HttpResponse(f, **response_args)
            response['Content-Disposition'] = 'attachment; filename=' + \
                filename_xlsx
            response['Cache-Control'] = 'no-cache'
            return response
        except Exception:
            return Response({"detail": _("Can't generate file")}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
