from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from dry_rest_permissions.generics import DRYPermissions


from bat.comments.models import Comment
from bat.comments import serializers
from bat.company.utils import get_member
from bat.globalutils.utils import has_any_permission


class BaseCommentViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.CommentSerializear
    queryset = Comment.objects.all()
    permission_classes = (IsAuthenticated, DRYPermissions,)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        company_id = self.kwargs.get("company_pk", None)
        object_id = self.kwargs.get("object_pk", None)
        request = self.request
        member = get_member(
            company_id=company_id,
            user_id=request.user.id,
        )
        content_type = self.get_content_type()
        return queryset.filter(
            content_type=content_type, object_id=object_id).order_by("posted")

    def create(self, request, company_pk, object_pk):
        member = get_member(company_id=company_pk, user_id=request.user.id)
        if not (has_any_permission(member, self.allow_create_permission_list)):
            return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content_type = self.get_content_type()
        serializer.save(user=request.user,
                        object_id=object_pk, content_type=content_type)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        company_pk = self.kwargs.get("company_pk", None)
        member = get_member(company_id=company_pk, user_id=request.user.id)
        if not (has_any_permission(member, self.allow_list_permission_list)):
            return Response({"detail": _("You do not have permission to perform this action.")}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
