"""
Database models for the News App.

This module defines the core data models used throughout the application.
All models inherit from Django's :class:`~django.db.models.Model` base class,
with the exception of :class:`CustomUser` which extends
:class:`~django.contrib.auth.models.AbstractUser`.

Models:
    - :class:`CustomUser` — extended user model with role-based access
    - :class:`Publisher` — represents a news organisation
    - :class:`Article` — a news article requiring editorial approval
    - :class:`Newsletter` — a curated collection of articles
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
        Extended user model that adds role-based access control.

    Inherits all standard Django user fields (``username``, ``email``,
    ``password``, etc.) from :class:`~django.contrib.auth.models.AbstractUser`
    and adds a ``role`` field along with subscription relationships
    specific to the News App.

    Three user roles are supported:

    - **Reader** — can browse and subscribe to publishers/journalists.
    - **Journalist** — can create articles and newsletters.
    - **Editor** — can approve, edit, and delete all articles and newsletters.

    Attributes:
        ROLE_CHOICES (list): Available role options as a list of
            ``(value, display)`` tuples.
        role (CharField): The user's assigned role. Defaults to ``'reader'``.
        subscribed_publishers (ManyToManyField): Publishers the reader follows.
            Related model: :class:`Publisher`.
        subscribed_journalists (ManyToManyField): Other users (journalists)
            the reader follows. Self-referential, asymmetric relationship.
        groups (ManyToManyField): Overrides the default ``groups`` field with
            a unique ``related_name`` to prevent clashing with other user models.
        user_permissions (ManyToManyField): Overrides the default
            ``user_permissions`` field with a unique ``related_name``.

    Example:
        Creating a journalist user::

            user = CustomUser.objects.create_user(
                username="jane",
                email="jane@news.com",
                password="securepass",
                role="journalist",
            )
    """

    # Role choices for our three user types

    ROLE_CHOICES = [
        ("reader", "Reader"),
        ("journalist", "Journalist"),
        ("editor", "Editor"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="reader")

    # Reader specific fields
    subscribed_publishers = models.ManyToManyField(
        "Publisher", blank=True, related_name="subscribers"
    )

    subscribed_journalists = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="followers"
    )

    # Override groups field with unique related_name
    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        # Add the unique name to stop the clashing
        related_name="customuser_set",
        related_query_name="customuser",
        help_text="The groups this user belongs to",
        verbose_name="groups",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        # This unique name stops the clash!
        related_name="customuser_set",
        related_query_name="customuser",
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class Publisher(models.Model):
    """
        Represents a news organisation or publication outlet.

    Publishers act as a grouping mechanism for articles and journalists.
    Readers can subscribe to publishers to receive articles from all
    journalists associated with that publisher.

    Attributes:
        name (CharField): The display name of the publisher organisation.
        journalists (ManyToManyField): Journalists affiliated with this
            publisher. Related to :class:`CustomUser`.
        editors (ManyToManyField): Editors affiliated with this publisher.
            Related to :class:`CustomUser`.
        created_at (DateTimeField): Timestamp set automatically when the
            publisher record is first created.

    Example:
        Creating a publisher and adding a journalist::

            publisher = Publisher.objects.create(name="The Daily News")
            publisher.journalists.add(journalist_user)
    """

    name = models.CharField(max_length=255)

    journalists = models.ManyToManyField(
        CustomUser, blank=True, related_name="journalist_publishers"
    )

    editors = models.ManyToManyField(
        CustomUser, blank=True, related_name="editor_publishers"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Article(models.Model):
    """
        A news article written by a journalist and subject to editor approval.

    Articles are created by journalists and must be approved by an editor
    before becoming publicly visible. Unapproved articles are only visible
    to the journalist who wrote them and to editors.

    Attributes:
        title (CharField): The headline of the article. Maximum 255 characters.
        content (TextField): The full body text of the article.
        author (ForeignKey): The :class:`CustomUser` who wrote the article.
            Deleting the author will cascade-delete their articles.
        publisher (ForeignKey): The optional :class:`Publisher` associated
            with this article. Set to ``NULL`` if the publisher is deleted.
        created_at (DateTimeField): Timestamp set automatically on creation.
        updated_at (DateTimeField): Timestamp updated automatically on each save.
        approved (BooleanField): Whether an editor has approved the article
            for public display. Defaults to ``False``.

    Meta:
        permissions: Adds a custom ``can_approve_article`` permission used
            by editors to approve articles.

    Example:
        Checking if an article is approved before rendering::

            article = Article.objects.get(pk=1)
            if article.approved:
                # Show to readers
    """

    title = models.CharField(max_length=255)
    content = models.TextField()

    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="articles"
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(default=False)

    class Meta:
        # Custom permission for editors
        permissions = [
            ("can_approve_article", "Can approve article"),
        ]

    def __str__(self):
        return f"{self.title} - {self.author.username}"


class Newsletter(models.Model):
    """
        A curated collection of articles assembled by a journalist.

    Newsletters allow journalists to group related approved articles into
    a single publication that readers can browse.

    Attributes:
        title (CharField): The title of the newsletter. Maximum 255 characters.
        description (TextField): A summary or introduction to the newsletter's content.
        author (ForeignKey): The :class:`CustomUser` (journalist) who created the
            newsletter. Deleting the author will cascade-delete their newsletters.
        articles (ManyToManyField): The :class:`Article` objects included in
            this newsletter. Blank (empty) newsletters are permitted.
        created_at (DateTimeField): Timestamp set automatically on creation.

    Example:
        Creating a newsletter and adding articles::

            newsletter = Newsletter.objects.create(
                title="Weekly Tech Roundup",
                description="Top tech stories this week.",
                author=journalist_user,
            )
            newsletter.articles.add(article1, article2)
    """

    title = models.CharField(max_length=255)
    description = models.TextField()

    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="newsletters"
    )

    articles = models.ManyToManyField(Article, blank=True, related_name="newsletters")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author.username}"
