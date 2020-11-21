from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, mixins, generics, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from bat.product import image_list_serializer, serializers
from bat.product.models import Image


class BaseImageViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):

    queryset = Image.objects.all()
    serializer_class = serializers.ImageSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["is_active"]

    def filter_queryset(self, queryset):
        return queryset.filter(
            object_id=self.kwargs.get(self.content_type + "_pk", None),
        )


class ProductImageViewSet(BaseImageViewSet):

    content_type = "product"


class BulkCreateModelMixin(mixins.CreateModelMixin):
    """
    Either create a single or many model instances in bulk by using the
    Serializers ``many=True`` ability from Django REST >= 2.2.5.
    .. note::
        This mixin uses the same method to create model instances
        as ``CreateModelMixin`` because both non-bulk and bulk
        requests will use ``POST`` request method.
    """

    def create(self, request, *args, **kwargs):
        bulk = isinstance(request.data, list)

        if not bulk:
            return super(BulkCreateModelMixin, self).create(request, *args, **kwargs)

        else:
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_bulk_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        return self.perform_create(serializer)


class ImageListViewset(BulkCreateModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    queryset = Image.objects.all()
    serializer_class = image_list_serializer.ImageSerializer
    content_type = "product"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["content_type"] = self.content_type
        kwargs = self.request.resolver_match.kwargs
        context["object_id"] = kwargs.get(self.content_type + "_pk", None)
        return context


class TestViewSet(viewsets.ViewSet):

    content_type = "product"

    def get_serializer_context(self):
        print("in context .....")
        context = super().get_serializer_context()
        context["content_type"] = self.content_type
        kwargs = self.request.resolver_match.kwargs
        context["object_id"] = kwargs.get(self.content_type + "_pk", None)
        return context

    def create(self, request, company_pk, product_pk):
        images_data = []
        for file_name, f in request.data.items():
            images_data.append({
                'file': f,
                'main_image': file_name == 'main_image',
            })
        if images_data:
            serializer = image_list_serializer.ImageSerializer(
                data=images_data, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
