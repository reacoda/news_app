from django.urls import path

# from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Home page
    path("", views.home_view, name="home"),
    # ==========================================
    # AUTHENTICATION URLs
    # ==========================================
    # /register/
    path("register/", views.register_view, name="register"),
    # /login/
    path("login/", views.CustomLoginView.as_view(), name="login"),
    # /logout/
    path("logout/", views.logout_view, name="logout"),
    # ==========================================
    # DASHBOARD URLs
    # ==========================================
    # /dashboard/
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # ==========================================
    # ARTICLE URLs
    # ==========================================
    # /articles/
    path("articles/", views.article_list_view, name="article_list"),
    # /articles/1/
    path("articles/<int:pk>/", views.article_detail_view, name="article_detail"),
    # /articles/create/
    path("articles/create/", views.create_article_view, name="create_article"),
    # /articles/1/edit/
    path("articles/<int:pk>/edit/", views.edit_article_view, name="edit_article"),
    # /articles/1/delete/
    path("articles/<int:pk>/delete/", views.delete_article_view, name="delete_article"),
    # /articles/1/approve/
    path(
        "articles/<int:pk>/approve/", views.approve_article_view, name="approve_article"
    ),
    # ==========================================
    # NEWSLETTER URLs
    # ==========================================
    # /newsletter/
    path("newsletter/", views.newsletter_list_view, name="newsletter_list"),
    # /newsletter/1/
    path(
        "newsletter/<int:pk>/", views.newsletter_detail_view, name="newsletter_detail"
    ),
    # /newsletter/create/
    path("newsletter/create/", views.create_newsletter_view, name="create_newsletter"),
    # /newsletter/1/edit/
    path(
        "newsletter/<int:pk>/edit/", views.edit_newsletter_view, name="edit_newsletter"
    ),
    # /newsletter/1/delete/
    path(
        "newsletter/<int:pk>/delete/",
        views.delete_newsletter_view,
        name="delete_newsletter",
    ),
    # ==========================================
    # SUBSCRIPTION URLs
    # ==========================================
    # /subscriptions/
    path("subscriptions/", views.subscription_view, name="subscriptions"),
    # /subscribe/publisher/1/
    path(
        "subscribe/publisher/<int:pk>/",
        views.subscribe_publisher_view,
        name="subscribe_publisher",
    ),
    # /subscribe/journalist/1/
    path(
        "subscribe/journalist/<int:pk>/",
        views.subscribe_journalist_view,
        name="subscribe_journalist",
    ),

    # ==========================================
    # PUBLISHER URLs
    # ==========================================

    # /publishers/
    path(
        'publishers/',
        views.publisher_list_view,
        name='publisher_list'
    ),

    # /publishers/create/
    path(
        'publishers/create/',
        views.create_publisher_view,
        name='create_publisher'
    ),

    # /publishers/<id>/join/
    path(
        'publishers/<int:pk>/join/',
        views.join_publisher_view,
        name='join_publisher'
    ),

    # /publishers/<id>/leave/
    path(
        'publishers/<int:pk>/leave/',
        views.leave_publisher_view,
        name='leave_publisher'
    ),
]
