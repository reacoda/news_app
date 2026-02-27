"""
This module registers the application's core models with the Django
admin site, making them manageable through the built-in admin interface
at ``/admin/``. Administrators can create, view, update, and delete
records for all registered models from this interface.

Models Registered:
    - :class:`~news_app.models.CustomUser`
    - :class:`~news_app.models.Article`
    - :class:`~news_app.models.Newsletter`
    - :class:`~news_app.models.Publisher`
"""
from django.contrib import admin
from .models import CustomUser, Article, Newsletter, Publisher

# Register models here
admin.site.register(CustomUser)
admin.site.register(Article)
admin.site.register(Newsletter)
admin.site.register(Publisher)
