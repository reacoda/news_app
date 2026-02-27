"""
Django application configuration for the news_app application.

This module contains the :class:`NewsAppConfig` class, which Django uses
to configure the ``news_app`` application on startup. It sets the default
primary key type for all models and performs any required initialisation
tasks when the application is ready.
"""

from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    """
    Application configuration class for the ``news_app`` Django application.

    This class is detected automatically by Django via the ``default_app_config``
    setting or the ``AppConfig`` discovery mechanism. It defines application-level
    metadata and startup behaviour.

    Attributes:
        default_auto_field (str): Specifies ``BigAutoField`` as the default
            type for auto-generated primary key fields across all models in
            this application.
        name (str): The Python dotted path to the application, used by Django
            to identify the app in ``INSTALLED_APPS``.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "news_app"

    def ready(self):
        """
        Perform initialisation tasks after the application registry is fully populated.

        This method is called automatically by Django once all apps have been
        loaded and the application registry is ready. It is the correct place
        to import and connect signals or perform other one-time setup.

        Note:
            Group creation is intentionally not performed here to avoid
            database access during startup. Use the ``setup_groups``
            management command instead to create user groups and assign
            permissions.
        """
        # Import signals here
        # Groups will be created by
        # a management command instead
        pass
