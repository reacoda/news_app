# news_app/management/commands/setup_groups.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    """
    Custom management command to create user groups
    and assign permissions.

    Run with: python manage.py setup_groups
    """

    help = "Creates user groups and assigns permissions"

    def handle(self, *args, **kwargs):
        """
        Main function that runs when command is called.
        """

        self.stdout.write("Creating groups...")

        # ---- CREATE GROUPS ----
        reader_group, created = Group.objects.get_or_create(name="Reader")
        if created:
            self.stdout.write("Reader group created")
        else:
            self.stdout.write("Reader group already exists")

        journalist_group, created = Group.objects.get_or_create(name="Journalist")
        if created:
            self.stdout.write("Journalist group created")
        else:
            self.stdout.write("Journalist group already exists")

        editor_group, created = Group.objects.get_or_create(name="Editor")
        if created:
            self.stdout.write("Editor group created")
        else:
            self.stdout.write("ℹEditor group already exists")

        # ---- ASSIGN PERMISSIONS ----

        # Reader permissions
        reader_permissions = [
            "view_article",
            "view_newsletter",
        ]

        # Journalist permissions
        journalist_permissions = [
            "view_article",
            "add_article",
            "change_article",
            "delete_article",
            "view_newsletter",
            "add_newsletter",
            "change_newsletter",
            "delete_newsletter",
        ]

        # Editor permissions
        editor_permissions = [
            "view_article",
            "change_article",
            "delete_article",
            "view_newsletter",
            "change_newsletter",
            "delete_newsletter",
            "can_approve_article",
        ]

        # Assign to each group
        self.assign_permissions(reader_group, reader_permissions)
        self.assign_permissions(journalist_group, journalist_permissions)
        self.assign_permissions(editor_group, editor_permissions)

        self.stdout.write(self.style.SUCCESS("All groups and permissions set up!"))

    def assign_permissions(self, group, codenames):
        """
        Assigns permissions to a group by codename.
        """
        for codename in codenames:
            try:
                permission = Permission.objects.get(codename=codename)
                group.permissions.add(permission)
                self.stdout.write(f"Added {codename} to {group.name}")
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Permission {codename} not found!")
                )
