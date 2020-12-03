from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

import djqscsv

from shutil import copyfile
import tempfile


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


class CsvExportMixin:

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
