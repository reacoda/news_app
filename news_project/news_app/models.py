from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser
    Adds role-based fields for Reader, Journalist and Editor.
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
    Represents a news organisation
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
    News article written by journalist.
    Requires editor approval before publishing
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
    Curated collection of articles by journalists
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
