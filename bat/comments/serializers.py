from rest_framework import serializers

from bat.users.serializers import UserSerializer
from bat.comments.models import Comment


class CommentSerializear(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "user", "parent", "content_type", "object_id",
                  "content", "posted", "edited")
        read_only_fields = ("id", "user", "parent", "content_type",
                            "object_id", "posted", "edited")
