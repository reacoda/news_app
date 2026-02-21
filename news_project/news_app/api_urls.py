from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import api_views

urlpatterns = [
    # ==========================================
    # AUTHENTICATION ENDPOINTS
    # ==========================================
    # POST /api/token/
    # Send username/password → get JWT token
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    # POST /api/token/refresh/
    # Send refresh token → get new access token
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # ==========================================
    # ARTICLE ENDPOINTS
    # ==========================================
    # GET/POST /api/articles/
    path("articles/", api_views.ArticleListView.as_view(), name="api_article_list"),
    # GET /api/articles/subscribed/
    path(
        "articles/subscribed/",
        api_views.SubscribedArticlesView.as_view(),
        name="api_subscribed_articles",
    ),
    # GET/PUT/DELETE /api/articles/<id>/
    path(
        "articles/<int:pk>/",
        api_views.ArticleDetailView.as_view(),
        name="api_article_detail",
    ),
    # POST /api/articles/<id>/approve/
    path(
        "articles/<int:pk>/approve/",
        api_views.approve_article_api,
        name="api_approve_article",
    ),
    # ==========================================
    # NEWSLETTER ENDPOINTS
    # ==========================================
    # GET/POST /api/newsletters/
    path(
        "newsletters/",
        api_views.NewsletterListView.as_view(),
        name="api_newsletter_list",
    ),
    # GET/PUT/DELETE /api/newsletters/<id>/
    path(
        "newsletters/<int:pk>/",
        api_views.NewsletterDetailView.as_view(),
        name="api_newsletter_detail",
    ),
]
