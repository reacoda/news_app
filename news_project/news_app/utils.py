"""
Utility functions for the News App.

This module provides helper functions used across the application for three
distinct concerns:

1. **Group and permission management** — creating Django user groups and
   assigning the correct permissions to each role.
2. **Email notifications** — sending emails to subscribers when an article
   is approved.
3. **Twitter/X integration** — posting a tweet when an article is approved.

All external service calls (email, Twitter) are wrapped in ``try/except``
blocks so that a failure in a notification does not prevent an article from
being approved (*graceful degradation*).

Functions:
    - :func:`create_groups_and_permissions`
    - :func:`assign_permissions`
    - :func:`assign_user_to_group`
    - :func:`send_approval_emails`
    - :func:`get_article_subscribers`
    - :func:`post_to_twitter`
"""

import requests
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import Group, Permission

# from django.contrib.contenttypes.models import ContentType

# =======================================
# Group management functions
# =======================================


def create_groups_and_permissions():
    """
    Create the three application user groups and assign permissions to each.

    Creates (or retrieves if already existing) the ``Reader``, ``Journalist``,
    and ``Editor`` groups and assigns the correct model-level permissions to
    each group using :func:`assign_permissions`.

    Note:
        This function should be called via the ``setup_groups`` management
        command rather than on app startup to avoid database access before
        migrations have run.
    """

    # ---- READER GROUP ----
    reader_group, created = Group.objects.get_or_create(name="Reader")

    # Readers can only VIEW
    reader_permissions = [
        "view_article",
        "view_newsletter",
    ]

    # ---- JOURNALIST GROUP ----
    journalist_group, created = Group.objects.get_or_create(name="Journalist")

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

    # ---- EDITOR GROUP ----
    editor_group, created = Group.objects.get_or_create(name="Editor")

    editor_permissions = [
        "view_article",
        "change_article",
        "delete_article",
        "view_newsletter",
        "change_newsletter",
        "delete_newsletter",
        # Custom permission we defined in Article model!
        "can_approve_article",
    ]

    # Assign permissions to each group
    assign_permissions(reader_group, reader_permissions)
    assign_permissions(journalist_group, journalist_permissions)
    assign_permissions(editor_group, editor_permissions)


def assign_permissions(group, permission_codenames):
    """
    Assign a list of permissions to a Django group.

    Iterates over the provided codenames and adds the corresponding
    :class:`~django.contrib.auth.models.Permission` objects to the group.
    If a permission codename does not exist in the database (e.g. migrations
    have not been run), a warning is printed and the loop continues.

    :param:
        group (django.contrib.auth.models.Group): The group to assign
            permissions to.
        permission_codenames (list[str]): A list of permission codename strings,
            e.g. ``["view_article", "add_article"]``.

    Example:
        ::

            journalist_group = Group.objects.get(name="Journalist")
            assign_permissions(journalist_group, ["add_article", "change_article"])
    """
    for codename in permission_codenames:
        try:
            permission = Permission.objects.get(codename=codename)
            group.permissions.add(permission)
        except Permission.DoesNotExist:
            # Permission not found - print warning
            print(f"Warning: Permission '{codename}' not found!")


def assign_user_to_group(user):
    """
    Assign a user to the Django group that matches their role.

    Clears the user from any existing groups first, then adds them to the
    correct group based on their ``role`` field (``'reader'``, ``'journalist'``,
    or ``'editor'``). Should be called immediately after a new user registers
    or when a user's role changes.

    :param:
        user (news_app.models.CustomUser): The user instance to assign to a group.
            Must have a valid ``role`` attribute.

    Note:
        If the target group does not exist (e.g. ``setup_groups`` has not been
        run), a warning is printed and no group is assigned.

    Example:
        Typical usage in a registration view::

            user = form.save()
            assign_user_to_group(user)
    """

    # Remove from all groups first
    user.groups.clear()

    # Map role to group name
    role_to_group = {
        "reader": "Reader",
        "journalist": "Journalist",
        "editor": "Editor",
    }

    # Get the correct group name
    group_name = role_to_group.get(user.role)

    if group_name:
        try:
            # Get group and add user to it
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            print(f"{user.username} added" f"to {group_name} group")
        except Group.DoesNotExist:
            print(f'Group "{group_name}"' f"not found! Run setup_groups")


# Email Notification Function


def send_approval_emails(article):
    """
    Send email notifications to relevant subscribers when an article is approved.

    Determines the appropriate subscriber list using
    :func:`get_article_subscribers`, builds a notification email, and sends
    it to all subscribers who have a valid email address on record.

    If no subscribers are found, or if the email send fails, the function
    exits gracefully without raising an exception. This ensures that article
    approval is never blocked by an email failure.

    Args:
        article (news_app.models.Article): The newly approved article.
            Must have ``title``, ``content``, and ``author`` attributes.

    Note:
        Uses Django's :func:`~django.core.mail.send_mail` function with the
        ``DEFAULT_FROM_EMAIL`` setting as the sender. Set this in
        ``settings.py`` before use.

    Example:
        Typically called inside an approval view or API function::

            article.approved = True
            article.save()
            send_approval_emails(article)
    """

    # Get list of subscribers to notify
    subscribers = get_article_subscribers(article)

    if not subscribers:
        print("ℹNo subscribers to notify")
        return

    # Build email content
    subject = f"New Article: {article.title}"

    message = f"""
    Hello!
  
    A new article has been published
    that you might be interested in:
   
    Title: {article.title}
    Author: {article.author.username}
    
    {article.content[:200]}...
    
    Read the full article on NewsApp!
    
    Best regards,
    The NewsApp Team
    """

    # Get list of subscriber emails
    subscriber_emails = [
        subscriber.email
        for subscriber in subscribers
        if subscriber.email  # Only if email exists
    ]

    if subscriber_emails:
        try:
            # Send ONE email to ALL subscribers
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=subscriber_emails,
                fail_silently=False,
            )
            print(f"Emails sent to " f"{len(subscriber_emails)} subscribers")

        except Exception as e:
            # Email failed but article still approved!
            # Graceful degradation!
            print(f"Email sending failed: {e}")


def get_article_subscribers(article):
    """
    Gets the correct list of subscribers
    based on whether article has a publisher
    or is independent.

    Scenario A: Article has publisher
    - Return subscribers of that publisher

    Scenario B: Independent article
    - Return subscribers of that journalist
    """

    if article.publisher:
        # SCENARIO A: Article belongs to publisher
        # Get readers subscribed to this publisher
        return article.publisher.subscribers.all()

    else:
        # SCENARIO B: Independent journalist article
        # Get readers subscribed to this journalist
        return article.author.followers.all()


# Twitter/X Integration


def post_to_twitter(article):
    """
    Post a tweet to X (Twitter) announcing a newly approved article.

    Builds a tweet from the article's title and author, truncates it to
    Twitter's 280-character limit if necessary, then sends it to the
    Twitter API v2 ``/2/tweets`` endpoint using a Bearer Token from
    Django settings.

    All exceptions are caught and logged without re-raising, so a Twitter
    failure never blocks article approval (*graceful degradation*).

    Args:
        article (news_app.models.Article): The approved article to announce.
            Must have ``title`` and ``author.username`` attributes.

    Raises:
        No exceptions are raised. All errors are caught internally and
        printed as warnings.

    Note:
        Requires ``TWITTER_BEARER_TOKEN`` to be set in ``settings.py``.
        This is Twitter's API Bearer Token, not a Django secret key.

    Example:
        Typically called alongside :func:`send_approval_emails` in an
        approval view::

            article.approved = True
            article.save()
            send_approval_emails(article)
            post_to_twitter(article)
    """

    try:
        # Build tweet text
        tweet_text = (
            f"New Article Published!\n\n"
            f"{article.title}\n\n"
            f"By: {article.author.username}\n\n"
            f"Read it on NewsApp! #NewsApp #News"
        )

        # Make sure tweet is under 280 chars
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

        # Twitter API v2 endpoint
        twitter_url = "https://api.twitter.com/2/tweets"

        # Make POST request to Twitter API
        response = requests.post(
            url=twitter_url,
            # Twitter Bearer Token for authorization
            # This is TWITTER'S key - not Django's!
            headers={
                "Authorization": (f"Bearer " f"{settings.TWITTER_BEARER_TOKEN}"),
                "Content-Type": "application/json",
            },
            # Tweet content
            json={"text": tweet_text},
        )

        # Check if tweet was successful
        if response.status_code == 201:
            print("Tweet posted successfully!")
        else:
            print(f"Tweet failed: " f"{response.status_code} " f"{response.text}")

    except requests.exceptions.ConnectionError:
        # Twitter is unreachable
        # Article still gets approved!
        print("Could not connect to Twitter")

    except requests.exceptions.Timeout:
        # Twitter took too long to respond
        print("Twitter request timed out")

    except Exception as e:
        # Any other unexpected error
        print(f"Twitter error: {e}")


