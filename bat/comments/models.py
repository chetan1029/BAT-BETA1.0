from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Comment(models.Model):
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, blank=True, null=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content = models.TextField()
    posted = models.DateTimeField(default=timezone.now, editable=False)
    edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        if not self.parent:
            return f'comment by {self.user} : {self.content[:20]}'
        else:
            return f'reply by {self.user} : {self.content[:20]}'

    @property
    def is_parent(self):
        return self.parent is None

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return self.content_object.has_read_permission(request) and self.content_object.has_read_permission(request)

    @staticmethod
    def has_list_permission(request):
        return True

    def has_object_list_permission(self, request):
        return self.content_object.has_read_permission(request) and self.content_object.has_read_permission(request)

    @staticmethod
    def has_create_permission(request):
        return True

    def has_object_create_permission(self, request):
        return True

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        return self.user == request.user

    @staticmethod
    def has_update_permission(request):
        return True

    def has_object_update_permission(self, request):
        return self.user == request.user
