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
    Only allows journalists to access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "journalist"


class IsEditor(BasePermission):
    """
    Only allows editors to access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "editor"


class IsEditorOrJournalist(BasePermission):
    """
    Allows editors AND journalists to access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            "journalist",
            "editor",
        ]


# ==========================================
# ARTICLE API VIEWS
# ==========================================


class ArticleListView(generics.ListCreateAPIView):
    """
    GET  /api/articles/ → List all approved articles
    POST /api/articles/ → Create article
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Article.objects.filter(approved=True).order_by("-created_at")

    def get_serializer_class(self):
        """
        Use ArticleCreateSerializer for INPUT
        Use ArticleSerializer for OUTPUT
        """
        if self.request.method == "POST":
            return ArticleCreateSerializer
        return ArticleSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsJournalist()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """
        Set author automatically!
        """
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override create to return full
        article details after creation!

        Steps:
        1. Use CreateSerializer for INPUT
        2. Save the article
        3. Return full ArticleSerializer
           for OUTPUT
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
    GET    /api/articles/<id>/ → Get single article
    PUT    /api/articles/<id>/ → Update article
    DELETE /api/articles/<id>/ → Delete article
    """

    serializer_class = ArticleSerializer

    def get_queryset(self):
        return Article.objects.filter(approved=True)

    def get_permissions(self):
        """
        GET: Any authenticated user
        PUT/DELETE: Editors or journalists only
        """
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsEditorOrJournalist()]


class SubscribedArticlesView(generics.ListAPIView):
    """
    GET /api/articles/subscribed/
    Returns articles ONLY from
    subscribed publishers/journalists.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Gets articles from subscribed
        publishers AND journalists only!
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
    POST /api/articles/<id>/approve/
    Approves article (editors only).
    Sends emails and posts to Twitter.
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
    GET  /api/newsletters/ → List all newsletters
    POST /api/newsletters/ → Create newsletter
    """

    serializer_class = NewsletterSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsJournalist()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Newsletter.objects.all().order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NewsletterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/newsletters/<id>/ → Get newsletter
    PUT    /api/newsletters/<id>/ → Update newsletter
    DELETE /api/newsletters/<id>/ → Delete newsletter
    """

    queryset = Newsletter.objects.all()
    serializer_class = NewsletterSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsEditorOrJournalist()]
