from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import ugettext_lazy as _


class ArchiveMixin:
    @action(detail=True, methods=["get"])
    def archive(self, request, *args, **kwargs):
        """Set the archive action."""
        instance = self.get_object()
        if not instance.is_active:
            return Response({"message": _("Already archived")}, status=status.HTTP_400_BAD_REQUEST)
        instance.is_active = False
        instance.save()
        return Response({"message": self.archive_message}, status=status.HTTP_200_OK)


class RestoreMixin:
    @action(detail=True, methods=["get"])
    def restore(self, request, *args, **kwargs):
        """Set the restore action."""
        instance = self.get_object()
        if instance.is_active:
            return Response({"message": _("Already active")}, status=status.HTTP_400_BAD_REQUEST)
        instance.is_active = True
        instance.save()
        return Response({"message": self.restore_message}, status=status.HTTP_200_OK)
