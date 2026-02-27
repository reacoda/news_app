"""
Django REST Framework serializers for the News App API.

This module defines serializers that convert model instances to and from
JSON representations used by the REST API. Nested serializers are used
to return full related-object details (e.g. author username, publisher name)
instead of bare integer IDs.

Serializers:
    - :class:`UserSerializer` — safe read-only representation of a user
    - :class:`PublisherSerializer` — representation of a publisher
    - :class:`ArticleSerializer` — full article details with nested relations
    - :class:`ArticleCreateSerializer` — minimal input serializer for creating articles
    - :class:`NewsletterSerializer` — newsletter with nested author and articles

Security Note:
    Password and other sensitive fields are intentionally excluded from
    all serializers. Never expose ``password`` in an API response.
"""

from rest_framework import serializers
from .models import CustomUser, Article, Newsletter, Publisher


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for :class:`~news_app.models.CustomUser`.

    Used as a **nested serializer** inside :class:`ArticleSerializer` and
    :class:`NewsletterSerializer` to embed author details directly in the
    API response rather than returning only a user ID.

    Only safe, non-sensitive fields are exposed. The ``password`` field
    is never included.

    Attributes:
        Meta.model (CustomUser): The model being serialized.
        Meta.fields (list): Exposed fields: ``id``, ``username``, ``email``, ``role``.
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
    Serializer for :class:`~news_app.models.Publisher`.

    Used as a **nested serializer** inside :class:`ArticleSerializer` to
    embed publisher details in article API responses.

    Attributes:
        Meta.model (Publisher): The model being serialized.
        Meta.fields (list): Exposed fields: ``id``, ``name``, ``created_at``.
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
    Full serializer for :class:`~news_app.models.Article`, used for API responses.

    Returns complete article data including nested ``author`` and ``publisher``
    objects rather than raw foreign key IDs. Both nested fields are read-only,
    meaning they cannot be set via this serializer — use
    :class:`ArticleCreateSerializer` for write operations instead.

    Attributes:
        author (UserSerializer): Nested read-only user object for the article author.
        publisher (PublisherSerializer): Nested read-only publisher object.
        Meta.model (Article): The model being serialized.
        Meta.fields (list): All exposed fields including nested objects.
        Meta.read_only_fields (list): Fields that cannot be set by API consumers:
            ``approved``, ``created_at``, ``updated_at``.

    Example:
        An example JSON response for a single article::

            {
                "id": 1,
                "title": "Breaking News",
                "content": "Full article text...",
                "author": {"id": 2, "username": "jane", "email": "...", "role": "journalist"},
                "publisher": {"id": 1, "name": "The Daily News", "created_at": "..."},
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z",
                "approved": true
            }
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
    Write-only serializer for creating a new :class:`~news_app.models.Article`.

    A simplified serializer used exclusively for the POST body when a journalist
    submits a new article. The ``author`` field is intentionally excluded
    because it is set automatically in the view from the authenticated user.

    Attributes:
        Meta.model (Article): The model being serialized.
        Meta.fields (list): Accepted input fields: ``title``, ``content``, ``publisher``.

    Note:
        After saving, :class:`ArticleSerializer` is used to build the full
        response body so that the client receives nested author/publisher details.
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
    Serializer for :class:`~news_app.models.Newsletter`.

    Returns full newsletter data including the nested ``author`` object and
    a list of nested ``articles``. Both nested fields are read-only.

    Attributes:
        author (UserSerializer): Nested read-only user object for the newsletter author.
        articles (ArticleSerializer): Nested read-only list of articles included
            in the newsletter.
        Meta.model (Newsletter): The model being serialized.
        Meta.fields (list): All exposed fields including nested objects.
        Meta.read_only_fields (list): The ``created_at`` field is read-only.

    Example:
        An example JSON response for a newsletter::

            {
                "id": 1,
                "title": "Weekly Roundup",
                "description": "Top stories this week.",
                "author": {"id": 2, "username": "jane", ...},
                "articles": [{"id": 1, "title": "...", ...}, ...],
                "created_at": "2025-01-01T10:00:00Z"
            }
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
