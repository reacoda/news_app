# news_app/serializers.py

from rest_framework import serializers
from .models import CustomUser, Article, Newsletter, Publisher


class UserSerializer(serializers.ModelSerializer):
    """
    Serializes CustomUser model.
    Used for displaying author details
    inside other serializers.
    """

    class Meta:
        model = CustomUser
        # Only expose safe fields!
        # Never expose password!
        fields = [
            "id",
            "username",
            "email",
            "role",
        ]


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializes Publisher model.
    """

    class Meta:
        model = Publisher
        fields = [
            "id",
            "name",
            "created_at",
        ]


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializes Article model.
    Uses nested serializers for author
    and publisher to return full details
    instead of just IDs!
    """

    # Nested serializer for author
    # Returns full user object not just ID!
    author = UserSerializer(read_only=True)

    # Nested serializer for publisher
    # read_only=True means API users
    # cannot change these via API
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",  # Returns full user object!
            "publisher",  # Returns full publisher object!
            "created_at",
            "updated_at",
            "approved",
        ]
        # These fields are set automatically
        # API users cannot change them!
        read_only_fields = [
            "approved",
            "created_at",
            "updated_at",
        ]


class ArticleCreateSerializer(serializers.ModelSerializer):
    """
    Separate serializer for CREATING articles.
    Simpler than ArticleSerializer.
    Author is set automatically in view!
    """

    class Meta:
        model = Article
        fields = [
            "title",
            "content",
            "publisher",
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializes Newsletter model.
    Includes nested author and articles.
    """

    # Nested author details
    author = UserSerializer(read_only=True)

    # Nested articles list
    articles = ArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "author",
            "articles",
            "created_at",
        ]
        read_only_fields = ["created_at"]
