from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class ArchiveMixin:
    @action(detail=True, methods=["get"])
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
    @action(detail=True, methods=["get"])
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
