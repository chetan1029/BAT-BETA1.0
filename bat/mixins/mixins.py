import tempfile
import djqscsv
import pandas as pd
from shutil import copyfile

from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse, StreamingHttpResponse

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
        if getattr(self, "csv_export_fields", None):
            queryset = queryset.values(*self.csv_export_fields)

        if getattr(self, "csv_field_header_map", None):
            return djqscsv.render_to_csv_response(
                queryset, append_datestamp=True, field_header_map=self.csv_field_header_map)
        else:
            return djqscsv.render_to_csv_response(
                queryset, append_datestamp=True)

    @action(detail=False, methods=["get"])
    def xlsxeport(self, request, *args, **kwargs):
        queryset = self.filter_queryset(
            self.get_queryset())
        if getattr(self, "csv_export_fields", None):
            queryset = queryset.values(*self.csv_export_fields)

        try:
            # get filenames
            filename_csv = djqscsv.generate_filename(queryset,
                                                     append_datestamp=True)
            filename_xlsx = ".".join(filename_csv.split(".")[:-1]) + ".xlsx"

            # Temporary files
            tmp_dir = tempfile.TemporaryDirectory()
            tmp_csv_file_path = tmp_dir.name + filename_csv
            tmp_xlsx_file_path = tmp_dir.name + filename_xlsx

            # create csv file
            csv_file = open(tmp_csv_file_path, "wb")
            if getattr(self, "csv_field_header_map", None):
                djqscsv.write_csv(queryset, csv_file,
                                  field_header_map=self.csv_field_header_map)
            else:
                djqscsv.write_csv(queryset, csv_file)
            csv_file.close()

            # convert csv file to xlsx file
            csv_file2 = open(tmp_csv_file_path, "r")
            df_new = pd.read_csv(csv_file2)
            df_new.to_excel(tmp_xlsx_file_path, index=False)

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


# class ImportMixin:

#     @action(detail=False, methods=["post"])
#     def xlsximportfile(self, request, *args, **kwargs):
#         file = request.data.get("file")
#         print("file...... :", type(file))

#         return Response({"detail": _("file")}, status=status.HTTP_200_OK)
