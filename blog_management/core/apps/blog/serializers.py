from rest_framework import serializers
from .models import Blog


class BlogSerializer(serializers.ModelSerializer):
    uploaded_image = serializers.ImageField(write_only=True, required=False)
    creator_username = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            'id',
            'title',
            'content',
            'uploaded_image',
            'image_url',
            'is_published',
            'published_at',
            'created_at',
            'creator_username',
        ]
        read_only_fields = [
            'id',
            'image_url',
            'is_published',
            'published_at',
            'created_at',
            'creator_username',
        ]

    def get_creator_username(self, obj):
        return obj.creator.username


class BlogUpdateSerializer(serializers.ModelSerializer):
    uploaded_image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Blog
        fields = ['title', 'content', 'uploaded_image']