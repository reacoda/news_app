# news_app/utils.py

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
    Creates the three user groups and assigns
    correct permissions to each group.
    Called automatically when app starts.
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
    Helper function to assign list of permissions
    to a specific group.
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
    Assigns a user to the correct group
    based on their role.
    Called when a new user registers.
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
    Sends email notifications when article
    is approved.

    Two scenarios:
    1. Article has publisher - email
       subscribers of that publisher
    2. Independent article - email
       subscribers of that journalist
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
    Posts approved article to X (Twitter).
    Uses Twitter API v2.

    Wrapped in try/except for graceful
    degradation - if Twitter fails,
    article approval still succeeds!
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
                "Authorization": (f"Bearer "
                                  f"{settings.TWITTER_BEARER_TOKEN}"),
                "Content-Type": "application/json",
            },
            # Tweet content
            json={"text": tweet_text},
        )

        # Check if tweet was successful
        if response.status_code == 201:
            print("Tweet posted successfully!")
        else:
            print(f"Tweet failed: " f"{response.status_code} "
                  f"{response.text}")

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
