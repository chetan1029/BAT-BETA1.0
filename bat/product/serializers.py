from rest_framework import serializers

from taggit.managers import TaggableManager

from bat.product.models import ProductParent


class TagField(serializers.Field):

    def to_representation(self, data):
        """
        List of group name.
        """
        if not isinstance(data, str):
            data = list(data.names())
        print("1 data........", data, " ", type(data))
        return data

    def to_internal_value(self, data):
        """
        return queryset of Group model from list of group name.
        """
        print("2 data........", data, " ", type(data))
        return data


class ProductParentSerializer(serializers.ModelSerializer):
    # tags = serializers.SerializerMethodField()
    tags = TagField(required=False)

    class Meta:
        model = ProductParent
        fields = "__all__"

    def get_tags(self, obj):
        """
        docstring
        """
        print("obj.tags..:", obj.tags)
        for i in obj.tags.names():
            print("i.......", i)
        return obj.tags.names()
