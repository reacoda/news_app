# news_app/apps.py

from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "news_app"

    def ready(self):
        """
        Called when Django starts up.
        Creates groups and permissions automatically.
        """
        # Import signals here
        # Groups will be created by
        # a management command instead
        pass
