from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Article, Newsletter
from .serializers import (
    ArticleSerializer,
    ArticleCreateSerializer,
    NewsletterSerializer,
)
from .utils import send_approval_emails, post_to_twitter

# ==========================================
# CUSTOM PERMISSION CLASSES
# ==========================================

from rest_framework.permissions import BasePermission


class IsJournalist(BasePermission):
    """
        Custom DRF permission that grants access to journalists only.

    A request is permitted if the user is authenticated and their
    ``role`` field is set to ``'journalist'``.

    Example:
        Used in :class:`ArticleListView` to restrict POST requests::

            def get_permissions(self):
                if self.request.method == "POST":
                    return [IsJournalist()]
                return [IsAuthenticated()]
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "journalist"


class IsEditor(BasePermission):
    """
    Custom DRF permission that grants access to editors only.

    A request is permitted if the user is authenticated and their
    ``role`` field is set to ``'editor'``.
    """

    def has_permission(self, request, view):
        """
        Check whether the requesting user is an authenticated editor.

        Args:
            request (rest_framework.request.Request): The incoming HTTP request.
            view (rest_framework.views.APIView): The view being accessed.

        Returns:
            bool: ``True`` if the user is authenticated and has role
            ``'editor'``, ``False`` otherwise.
        """
        return request.user.is_authenticated and request.user.role == "editor"


class IsEditorOrJournalist(BasePermission):
    """
      Custom DRF permission that grants access to both editors and journalists.

    A request is permitted if the user is authenticated and their
    ``role`` field is either ``'editor'`` or ``'journalist'``.
    """

    def has_permission(self, request, view):
        """
         Check whether the requesting user is an authenticated editor or journalist.

        Args:
            request (rest_framework.request.Request): The incoming HTTP request.
            view (rest_framework.views.APIView): The view being accessed.

        Returns:
            bool: ``True`` if the user is authenticated and has role
            ``'editor'`` or ``'journalist'``, ``False`` otherwise.
        """
        return request.user.is_authenticated and request.user.role in [
            "journalist",
            "editor",
        ]


# ==========================================
# ARTICLE API VIEWS
# ==========================================


class ArticleListView(generics.ListCreateAPIView):
    """
    API view for listing and creating articles.

    **GET** ``/api/articles/`` — Returns all approved articles ordered by
    most recently created. Requires any authenticated user.

    **POST** ``/api/articles/`` — Creates a new article. Requires the
    requesting user to have the ``'journalist'`` role. The article author
    is set automatically to the requesting user.

    Permissions:
        - GET: Any authenticated user (:class:`IsAuthenticated`)
        - POST: Journalists only (:class:`IsJournalist`)

    Serializers:
        - Input (POST): :class:`~news_app.serializers.ArticleCreateSerializer`
        - Output (GET/POST response): :class:`~news_app.serializers.ArticleSerializer`
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return all approved articles ordered by creation date (newest first).

        Returns:
            QuerySet: Approved :class:`~news_app.models.Article` objects,
            ordered by ``-created_at``.
        """
        return Article.objects.filter(approved=True).order_by("-created_at")

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the HTTP method.

        Uses :class:`~news_app.serializers.ArticleCreateSerializer` for
        write operations (POST) and :class:`~news_app.serializers.ArticleSerializer`
        for read operations (GET).

        Returns:
            type: The serializer class to use for this request.
        """
        if self.request.method == "POST":
            return ArticleCreateSerializer
        return ArticleSerializer

    def get_permissions(self):
        """
        Return the permission instances required for this request.

        POST requests require the :class:`IsJournalist` permission.
        All other requests (GET) require any authenticated user.

        Returns:
            list: A list of instantiated permission objects.
        """
        if self.request.method == "POST":
            return [IsJournalist()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        Save the new article with the requesting user set as the author.

        This override ensures the ``author`` field is populated automatically
        from the authenticated user rather than being supplied in the request body.

        :param:
            serializer (ArticleCreateSerializer): The validated serializer
                instance ready to be saved.
        """
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Handle POST request to create a new article.

        Overrides the default ``create`` method to use
        :class:`~news_app.serializers.ArticleCreateSerializer` for input
        validation and :class:`~news_app.serializers.ArticleSerializer`
        for the response body, so the full article details (including
        nested author and publisher objects) are returned after creation.

        Args:
            request (rest_framework.request.Request): The incoming POST request
                containing article data (``title``, ``content``, ``publisher``).
            *args: Variable length argument list passed to the parent method.
            **kwargs: Arbitrary keyword arguments passed to the parent method.

        Returns:
            rest_framework.response.Response: HTTP 201 Created with the full
            article data if valid, or HTTP 400 Bad Request with validation
            errors if invalid.
        """
        # Use create serializer for input
        create_serializer = ArticleCreateSerializer(data=request.data)

        if create_serializer.is_valid():
            # Save article with author
            article = create_serializer.save(author=request.user)

            # Return FULL details using
            # ArticleSerializer for output!
            response_serializer = ArticleSerializer(
                article, context={"request": request}
            )

            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a single article.

    **GET** ``/api/articles/<id>/`` — Retrieve a single approved article.
    Requires any authenticated user.

    **PUT** ``/api/articles/<id>/`` — Update an article. Requires the
    requesting user to be an editor or journalist.

    **DELETE** ``/api/articles/<id>/`` — Delete an article. Requires the
    requesting user to be an editor or journalist.

    Permissions:
        - GET: Any authenticated user (:class:`IsAuthenticated`)
        - PUT / DELETE: Editors or journalists (:class:`IsEditorOrJournalist`)

    Note:
        Only approved articles are accessible via this view.
    """

    serializer_class = ArticleSerializer

    def get_queryset(self):
        """
        Return all approved articles available for retrieval.

        Returns:
            QuerySet: Approved :class:`~news_app.models.Article` objects.
        """
        return Article.objects.filter(approved=True)

    def get_permissions(self):
        """
        Return the permission instances required for this request.

        GET requests require any authenticated user. PUT and DELETE
        requests require an editor or journalist role.

        Returns:
            list: A list of instantiated permission objects.
        """
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsEditorOrJournalist()]


class SubscribedArticlesView(generics.ListAPIView):
    """
    API view that returns articles from a reader's subscribed sources.

    **GET** ``/api/articles/subscribed/`` — Returns approved articles
    whose publisher or author the requesting user has subscribed to.

    Uses Django ``Q`` objects to perform an OR query across subscribed
    publishers and subscribed journalists in a single database query.

    Permissions:
        - GET: Any authenticated user (:class:`IsAuthenticated`)
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return approved articles from the user's subscribed publishers and journalists.

        Fetches the requesting user's ``subscribed_publishers`` and
        ``subscribed_journalists`` ManyToMany relationships, then returns
        all approved articles that belong to either group, ordered newest first.

        Returns:
            QuerySet: Approved :class:`~news_app.models.Article` objects
            filtered by the user's subscriptions, ordered by ``-created_at``.
        """
        user = self.request.user

        # Get subscribed publishers
        subscribed_publishers = user.subscribed_publishers.all()

        # Get subscribed journalists
        subscribed_journalists = user.subscribed_journalists.all()

        # Get articles from BOTH sources
        # Q objects allow OR queries!
        articles = Article.objects.filter(
            Q(publisher__in=subscribed_publishers)
            | Q(author__in=subscribed_journalists),
            approved=True,
        ).order_by("-created_at")

        return articles


@api_view(["POST"])
def approve_article_api(request, pk):
    """
    Approve an article and trigger notification side-effects.

    **POST** ``/api/articles/<id>/approve/``

    Only users with the ``'editor'`` role may approve articles.
    On successful approval the following side-effects are triggered:

    1. Email notifications are sent to all relevant subscribers via
       :func:`~news_app.utils.send_approval_emails`.
    2. A tweet is posted to X (Twitter) via
       :func:`~news_app.utils.post_to_twitter`.

    Args:
        request (rest_framework.request.Request): The incoming POST request.
            The requesting user must have ``role == 'editor'``.
        pk (int): The primary key of the :class:`~news_app.models.Article`
            to approve.

    Returns:
        rest_framework.response.Response:
            - HTTP 200 OK with a success message and the full article data
              if the article was approved successfully.
            - HTTP 403 Forbidden if the requesting user is not an editor.
            - HTTP 404 Not Found if no article with the given ``pk`` exists.
    """
    # Check user is editor
    if request.user.role != "editor":
        return Response(
            {"error": "Only editors can approve"}, status=status.HTTP_403_FORBIDDEN
        )

    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response(
            {"error": "Article not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Approve the article
    article.approved = True
    article.save()

    # Send emails to subscribers
    send_approval_emails(article)

    # Post to Twitter
    post_to_twitter(article)

    return Response(
        {"message": "Article approved!", "article": ArticleSerializer(article).data},
        status=status.HTTP_200_OK,
    )


# ==========================================
# NEWSLETTER API VIEWS
# ==========================================


class NewsletterListView(generics.ListCreateAPIView):
    """
    API view for listing and creating newsletters.

    **GET** ``/api/newsletters/`` — Returns all newsletters ordered by
    most recently created. Requires any authenticated user.

    **POST** ``/api/newsletters/`` — Creates a new newsletter. Requires
    the requesting user to have the ``'journalist'`` role. The author
    is set automatically to the requesting user.

    Permissions:
        - GET: Any authenticated user (:class:`IsAuthenticated`)
        - POST: Journalists only (:class:`IsJournalist`)
    """

    serializer_class = NewsletterSerializer

    def get_permissions(self):
        """
        Return the permission instances required for this request.

        POST requests require the :class:`IsJournalist` permission.
        All other requests require any authenticated user.

        Returns:
            list: A list of instantiated permission objects.
        """
        if self.request.method == "POST":
            return [IsJournalist()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """
        Return all newsletters ordered by creation date (newest first).

        Returns:
            QuerySet: All :class:`~news_app.models.Newsletter` objects,
            ordered by ``-created_at``.
        """
        return Newsletter.objects.all().order_by("-created_at")

    def perform_create(self, serializer):
        """
        Save the new newsletter with the requesting user set as author.

        :param:
            serializer (NewsletterSerializer): The validated serializer
                instance ready to be saved.
        """
        serializer.save(author=self.request.user)


class NewsletterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a single newsletter.

    **GET** ``/api/newsletters/<id>/`` — Retrieve a newsletter.
    Requires any authenticated user.

    **PUT** ``/api/newsletters/<id>/`` — Update a newsletter.
    Requires editor or journalist role.

    **DELETE** ``/api/newsletters/<id>/`` — Delete a newsletter.
    Requires editor or journalist role.

    Permissions:
        - GET: Any authenticated user (:class:`IsAuthenticated`)
        - PUT / DELETE: Editors or journalists (:class:`IsEditorOrJournalist`)
    """

    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsEditorOrJournalist()]
