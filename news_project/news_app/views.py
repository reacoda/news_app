"""
Browser-facing (HTML) views for the News App.

This module contains all Django view functions and class-based view that render
HTML templates for the web interface. It handles authentication,
role-based dashboards, articles and newsletter management, subscriptions,
and publisher management.

"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.views import LoginView

from .models import CustomUser, Article, Newsletter, Publisher
from .forms import UserRegistrationForm, ArticleForm, NewsletterForm
from .utils import assign_user_to_group, send_approval_emails, post_to_twitter

# Homepage view


def home_view(request):
    """
    Render the application landing page.
    Authenticated users are redirected to their dashboard immediately.
    Unauthenticated visitors see the public landing page.

    :param:
        request(django.http.HttpRequest): The incoming HTTP request.

    Returns:
        django.http.HttpRequest: A redirect to 'dashboard' for
        authenticated users, or a rendered 'news_app/home.html' template
        for visitors.
    """
    # If already logged in go to dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")

    # Show landing page to visitors
    return render(request, "news_app/home.html", {})


# Authentication Views


def register_view(request):
    """
    Handles new user registration

    Displays a registration form on GET requests. On a valid POST submission,
    creates the new user, sets their role, assigns them to the correct
    permission group via :func: news_app.utils.assign_user_to_group, logs them
    in automatically, and redirects to the dashboard.

    Authenticated user who visit this view are redirected to the dashboard
    without seeing the form.

    :param:
        request(django.http.HttpRequest): The incoming HTTP request.
        POST body should include 'username', 'email', 'role',
        'password1', and 'password2'.

    Returns:
        django.http.HttpResponse:
            - Redirect to 'dashboard' on successful registration.
            - Redirect to 'dashboard' if user is already authenticated
            - Rendered 'news_app/register.html' with the form on GET, or
            on POST if the form contains validation errors
    """
    # If already logged in, go to dashboard
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        # GET form data from request
        form = UserRegistrationForm(request.POST)

        # Validate form
        if form.is_valid():
            # Save user but don't commit
            # Need to set role first
            user = form.save(commit=False)

            # SET role from form data
            user.role = form.cleaned_data["role"]

            # Now we can save to database
            user.save()

            # Assign user to correct group based on their role
            assign_user_to_group(user)

            # Login user automatically
            login(request, user)

            # Show success message
            messages.success(request, f"Welcome to NewsApp, {user.username}!")

            # Redirect to dashboard
            return redirect("dashboard")

        else:
            # Form has errors
            messages.error(request, "Please fix the errors below")
    else:
        # GET request - show empty form
        form = UserRegistrationForm()

    return render(request, "news_app/register.html", {"form": form})


class CustomLoginView(LoginView):
    """
    Custom login view that extends Django's
    built-in :class:`django.contrib.auth.views.LoginView`

    Renders the applications's login template and redirects
    already-authenticated users directly to the dashboard.
    All login logic (credential validation, session creation) is
    handled by the parent class.

    Attributes:
        template_name (str): Path to the login HTML template.
        redirect_authenticated_user (bool): if True, authenticated users
        visiting the login page are redirected to ``get_success_url()``
    """

    template_name = "news_app/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful login.

        Returns:
            str: The relative URL '/dashboard'
        """
        return "/dashboard"


def logout_view(request):
    """
    Log out the current user and redirect to the login page.

    Calls Django's :func: 'django.contrib.auth.logout' to clear
    the session, the shows an informational message and redirects.

    :param:
        request(django.http.HttpRequest): The incoming HTTP request.

    Request:
        django.http.HttpResponseRedirect: A redirect to the 'login' URL.

    """
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect("login")


# Dashboard View


@login_required
def dashboard_view(request):
    """
     Render the role-specific dashboard for the authenticated user.

    The context data passed to the template differs depending on the user's role:

    - Journalist: their own articles ordered by most recent.
    - Editor: all pending (unapproved) and approved articles.
    - Reader: their subscribed publishers and journalists.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
            The user must be authenticated (enforced by ``@login_required``).

    Returns:
        django.http.HttpResponse: Rendered ``news_app/dashboard.html`` with
        role-appropriate context data.
    """
    user = request.user
    context = {"user": user}

    if user.role == "journalist":
        # Get journalist's own articles
        context["articles"] = Article.objects.filter(author=user).order_by(
            "-created_at"
        )

    elif user.role == "editor":
        # Get articles pending approval
        context["pending_articles"] = Article.objects.filter(approved=False).order_by(
            "-created_at"
        )
        context["approved_articles"] = Article.objects.filter(approved=True).order_by(
            "-created_at"
        )

    elif user.role == "reader":
        # Get subscribed content
        context["subscribed_publishers"] = user.subscribed_publishers.all()
        context["subscribed_journalists"] = user.subscribed_journalists.all()

    return render(request, "news_app/dashboard.html", context)


# Article View


def article_list_view(request):
    """
    Display a list of all approved articles.

    Publicly accessible - no authentication required. Only articles with
    `approved=True` are shown, ordered newes first.

    :param:
        request(django.http.HttpRequest): The incoming HTTP request.

    Returns:
        django.http.HttpResponse: Rendered `news_app/article_list.html`
        with a QuerySet of approved articles in the context under `'articles'`.
    """
    # Only get approved articles
    articles = Article.objects.filter(approved=True).order_by("-created_at")

    return render(request, "news_app/article_list.html", {"articles": articles})


def article_detail_view(request, pk):
    """
        Display the full detail page for a single approved article.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the article to display.

    Returns:
        django.http.HttpResponse: Rendered ``news_app/article_detail.html``
        with the article in the context under ``'article'``.

    Raises:
        django.http.Http404: If no approved article with the
        given ``pk`` exists.
    """
    # get_object_or_404 handles wrong IDs
    article = get_object_or_404(Article, pk=pk, approved=True)

    return render(request, "news_app/article_detail.html", {"article": article})


@login_required
@permission_required("news_app.add_article", raise_exception=True)
def create_article_view(request):
    """
    Allow a journalist to create a new article.

    Requires the user to be logged in and to have the ``add_article``
    permission (assigned to the Journalist group). On a valid POST
    submission, the article is saved with the requesting user set as the
    author and redirected to the dashboard with a success message.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'dashboard'`` after successful creation.
            - Rendered ``news_app/article_form.html`` with the form and
              ``action='Create'`` on GET, or on invalid POST.
    """

    if request.method == "POST":
        form = ArticleForm(request.POST)

        if form.is_valid():
            # Save article but don't save to database yet
            # Still need to set author first
            article = form.save(commit=False)

            # Set author automatically
            # to logged in journalist
            article.author = request.user

            # Save to database
            article.save()

            # Success message
            messages.success(request, "Article submitted for approval!")
            return redirect("dashboard")

    else:
        form = ArticleForm()

    return render(
        request, "news_app/article_form.html", {"form": form, "action": "Create"}
    )


@login_required
@permission_required("news_app.change_article", raise_exception=True)
def edit_article_view(request, pk):
    """
    Allow a journalist or editor to edit an existing article.

    Journalists may only edit their own articles. Editors may edit any article.
    If a journalist attempts to edit an article they do not own, they are
    redirected to the dashboard with an error message.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the article to edit.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'dashboard'`` after successful update.
            - Redirect to ``'dashboard'`` if a journalist tries to edit
              another journalist's article.
            - Rendered ``news_app/article_form.html`` with the populated form
              and ``action='Edit'`` on GET, or on invalid POST.

    Raises:
        django.http.Http404: If no article with the given ``pk`` exists.
    """
    article = get_object_or_404(Article, pk=pk)

    # Journalist can only edit OWN articles
    if request.user.role == "journalist":
        if article.author != request.user:
            messages.error(request, "You can only edit your own articles!")
            return redirect("dashboard")

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated successfully!")
            # Redirect to dashboard
            return redirect("dashboard")
    else:
        form = ArticleForm(instance=article)

    return render(
        request, "news_app/article_form.html", {"form": form, "action": "Edit"}
    )


@login_required
@permission_required("news_app.can_approve_article", raise_exception=True)
def approve_article_view(request, pk):
    """
        Allow an editor to approve a pending article.

    On a POST submission, sets ``article.approved = True``, saves the record,
    then triggers two side-effects:

    1. Email notifications to subscribers via
    :func:`~news_app.utils.send_approval_emails`.
    2. A tweet posted to X (Twitter) via
    :func:`~news_app.utils.post_to_twitter`.

    Requires the ``can_approve_article`` permission (assigned to the Editor group).

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the article to approve.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'dashboard'`` after successful approval.
            - Rendered ``news_app/approve_article.html`` with the article
              in context on GET (confirmation page).

    Raises:
        django.http.Http404: If no article with the given ``pk`` exists.
    """
    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        # Approve the article
        article.approved = True
        article.save()

        # Send emails to subscribers
        send_approval_emails(article)

        # Post to X (Twitter)
        post_to_twitter(article)

        messages.success(request, f'Article "{article.title}" approved!')
        return redirect("dashboard")

    return render(request, "news_app/approve_article.html", {"article": article})


@login_required
@permission_required("news_app.delete_article", raise_exception=True)
def delete_article_view(request, pk):
    """
    Allow a journalist or editor to delete an article.

    Journalists may only delete their own articles. If a journalist attempts
    to delete an article they do not own, they are redirected to the dashboard
    with an error message.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the article to delete.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'dashboard'`` after successful deletion.
            - Redirect to ``'dashboard'`` if a journalist tries to delete
              another journalist's article.
            - Rendered ``news_app/delete_confirm.html`` with the article
              in context on GET (confirmation page).

    Raises:
        django.http.Http404: If no article with the given ``pk`` exists.
    """
    article = get_object_or_404(Article, pk=pk)

    # Journalist can only delete OWN articles
    if request.user.role == "journalist":
        if article.author != request.user:
            messages.error(request, "You can only delete your own articles!")
            return redirect("dashboard")

    if request.method == "POST":
        article.delete()
        messages.success(request, "Article deleted successfully!")
        return redirect("dashboard")

    return render(request, "news_app/delete_confirm.html", {"article": article})


# ==========================================
# NEWSLETTER VIEWS
# ==========================================


def newsletter_list_view(request):
    """
        Display a list of all newsletters.

    Publicly accessible — no authentication required. All newsletters are
    shown, ordered newest first.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.

    Returns:
        django.http.HttpResponse: Rendered ``news_app/newsletter_list.html``
        with all newsletters in the context under ``'newsletters'``.
    """
    newsletters = Newsletter.objects.all().order_by("-created_at")

    return render(
        request, "news_app/newsletter_list.html", {"newsletters": newsletters}
    )


def newsletter_detail_view(request, pk):
    """
    Display the full detail page for a single newsletter.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the newsletter to display.

    Returns:
        django.http.HttpResponse: Rendered ``news_app/newsletter_detail.html``
        with the newsletter in the context under ``'newsletter'``.

    Raises:
        django.http.Http404: If no newsletter with the given ``pk`` exists.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    return render(
        request, "news_app/newsletter_detail.html", {"newsletter": newsletter}
    )


@login_required
@permission_required("news_app.add_newsletter", raise_exception=True)
def create_newsletter_view(request):
    """
    Allow a journalist to create a new newsletter.

    On a valid POST submission, saves the newsletter with the requesting user
    as the author and calls ``form.save_m2m()`` to persist the ManyToMany
    ``articles`` relationship.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.

    Returns:
        django.http.HttpResponse:
            - Redirect to the new newsletter's detail page on success.
            - Rendered ``news_app/newsletter_form.html`` with the form and
              ``action='Create'`` on GET, or on invalid POST.
    """
    if request.method == "POST":
        form = NewsletterForm(request.POST)

        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()

            # Save ManyToMany articles field
            form.save_m2m()

            messages.success(request, "Newsletter created successfully!")
            return redirect("newsletter_detail", pk=newsletter.pk)
    else:
        form = NewsletterForm()

    return render(
        request, "news_app/newsletter_form.html", {"form": form, "action": "Create"}
    )


@login_required
@permission_required("news_app.change_newsletter", raise_exception=True)
def edit_newsletter_view(request, pk):
    """
        Allow a journalist or editor to edit an existing newsletter.

    Journalists may only edit their own newsletters. Editors may edit any
    newsletter. If a journalist attempts to edit a newsletter they do not
    own, they are redirected to the newsletter list with an error message.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the newsletter to edit.

    Returns:
        django.http.HttpResponse:
            - Redirect to the newsletter's detail page after successful update.
            - Redirect to ``'newsletter_list'`` if a journalist tries to edit
              another journalist's newsletter.
            - Rendered ``news_app/newsletter_form.html`` with the populated
              form and ``action='Edit'`` on GET, or on invalid POST.

    Raises:
        django.http.Http404: If no newsletter with the given ``pk`` exists.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    # Journalist can only edit OWN newsletters
    if request.user.role == "journalist":
        if newsletter.author != request.user:
            messages.error(request, "You can only edit your own newsletters!")
            return redirect("newsletter_list")

    if request.method == "POST":
        form = NewsletterForm(request.POST, instance=newsletter)
        if form.is_valid():
            form.save()
            messages.success(request, "Newsletter updated!")
            return redirect("newsletter_detail", pk=pk)
    else:
        form = NewsletterForm(instance=newsletter)

    return render(
        request, "news_app/newsletter_form.html", {"form": form, "action": "Edit"}
    )


@login_required
@permission_required("news_app.delete_newsletter", raise_exception=True)
def delete_newsletter_view(request, pk):
    """
    Allow a journalist or editor to delete a newsletter.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the newsletter to delete.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'newsletter_list'`` after successful deletion.
            - Rendered ``news_app/delete_confirm.html`` with the newsletter
              in context on GET (confirmation page).

    Raises:
        django.http.Http404: If no newsletter with the given ``pk`` exists.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if request.method == "POST":
        newsletter.delete()
        messages.success(request, "Newsletter deleted!")
        return redirect("newsletter_list")

    return render(request, "news_app/delete_confirm.html", {"newsletter": newsletter})


# ==========================================
# SUBSCRIPTION VIEWS
# ==========================================


@login_required
def subscription_view(request):
    """
    Display the subscription management page for the current user.

    Lists all available publishers and journalists so the user can
    subscribe or unsubscribe as they wish.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
            User must be authenticated.

    Returns:
        django.http.HttpResponse: Rendered ``news_app/subscriptions.html``
        with ``'publishers'`` and ``'journalists'`` QuerySets in the context.
    """
    # Get all publishers and journalists
    publishers = Publisher.objects.all()
    journalists = CustomUser.objects.filter(role="journalist")

    return render(
        request,
        "news_app/subscriptions.html",
        {
            "publishers": publishers,
            "journalists": journalists,
        },
    )


@login_required
def subscribe_publisher_view(request, pk):
    """
    Toggle the current user's subscription to a publisher.

    If the user is already subscribed to the publisher, they are unsubscribed.
    Otherwise, they are subscribed. Always redirects back to the subscriptions
    page after the toggle.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the :class:`~news_app.models.Publisher`
            to subscribe or unsubscribe from.

    Returns:
        django.http.HttpResponseRedirect: A redirect to ``'subscriptions'``.

    Raises:
        django.http.Http404: If no publisher with the given ``pk`` exists.
    """
    publisher = get_object_or_404(Publisher, pk=pk)

    # Toggle subscription
    if publisher in request.user.subscribed_publishers.all():
        request.user.subscribed_publishers.remove(publisher)
        messages.info(request, f"Unsubscribed from {publisher.name}")
    else:
        request.user.subscribed_publishers.add(publisher)
        messages.success(request, f"Subscribed to {publisher.name}!")

    return redirect("subscriptions")


@login_required
def subscribe_journalist_view(request, pk):
    """
     Toggle the current user's subscription (follow) to a journalist.

    If the user already follows the journalist, they are unfollowed.
    Otherwise, they begin following them.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the journalist
            (:class:`~news_app.models.CustomUser` with ``role='journalist'``)
            to follow or unfollow.

    Returns:
        django.http.HttpResponseRedirect: A redirect to ``'subscriptions'``.

    Raises:
        django.http.Http404: If no journalist user with
        the given ``pk`` exists.
    """
    journalist = get_object_or_404(CustomUser, pk=pk, role="journalist")

    # Toggle subscription
    if journalist in request.user.subscribed_journalists.all():
        request.user.subscribed_journalists.remove(journalist)
        messages.info(request, f"Unfollowed {journalist.username}")
    else:
        request.user.subscribed_journalists.add(journalist)
        messages.success(request, f"Following {journalist.username}!")

    return redirect("subscriptions")


# ==========================================
# Publisher Management Views
# ==========================================


@login_required
def publisher_list_view(request):
    """
    Display a list of all publishers, sorted alphabetically by name.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
            User must be authenticated.

    Returns:
        django.http.HttpResponse: Rendered ``news_app/publisher_list.html``
        with a QuerySet of all publishers in the context under ``'publishers'``.
    """
    publishers = Publisher.objects.all().order_by("name")

    return render(request, "news_app/publisher_list.html", {"publishers": publishers})


@login_required
# @permission_required(
#     'news_app.add_publisher',
#     raise_exception=True
# )
def create_publisher_view(request):
    """
        Allow an authenticated user to create a new publisher.

    Reads the publisher ``name`` directly from ``request.POST``. If the name
    is present and non-empty, a new :class:`~news_app.models.Publisher` record
    is created and the user is redirected to the publisher list.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
            POST body should include ``'name'``.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'publisher_list'`` on successful creation.
            - Rendered ``news_app/publisher_form.html`` with ``action='Create'``
              on GET, or if the name field was empty on POST.
    """
    if request.method == "POST":
        name = request.POST.get("name")

        if name:
            publisher = Publisher.objects.create(name=name)
            messages.success(request, f'Publisher "{name}" created successfully!')
            return redirect("publisher_list")
        else:
            messages.error(request, "Publisher name is required!")

    return render(request, "news_app/publisher_form.html", {"action": "Create"})


@login_required
def join_publisher_view(request, pk):
    """
    Allow a journalist or editor to join a publisher organisation.

    On POST, adds the requesting user to the publisher's ``journalists`` or
    ``editors`` ManyToMany field based on their role. Readers receive an error
    message and are not added.

    :param:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the publisher to join.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'publisher_list'`` after joining.
            - Rendered ``news_app/publisher_join_confirm.html`` with the
              publisher in context on GET (confirmation page).

    Raises:
        django.http.Http404: If no publisher with the given ``pk`` exists.
    """
    publisher = get_object_or_404(Publisher, pk=pk)

    if request.method == "POST":
        # Add user to publisher based on role
        if request.user.role == "journalist":
            publisher.journalists.add(request.user)
            messages.success(request, f"You joined {publisher.name} as a journalist!")
        elif request.user.role == "editor":
            publisher.editors.add(request.user)
            messages.success(request, f"You joined {publisher.name} as an editor!")
        else:
            messages.error(request, "Only journalists and editors can join publishers!")

        return redirect("publisher_list")

    return render(
        request, "news_app/publisher_join_confirm.html", {"publisher": publisher}
    )


@login_required
def leave_publisher_view(request, pk):
    """
    Allow a journalist or editor to leave a publisher organisation.

    On POST, removes the requesting user from the publisher's ``journalists``
    or ``editors`` ManyToMany field based on their role.

    Args:
        request (django.http.HttpRequest): The incoming HTTP request.
        pk (int): The primary key of the publisher to leave.

    Returns:
        django.http.HttpResponse:
            - Redirect to ``'publisher_list'`` after leaving.
            - Rendered ``news_app/publisher_leave_confirm.html`` with the
              publisher in context on GET (confirmation page).

    Raises:
        django.http.Http404: If no publisher with the given ``pk`` exists.
    """
    publisher = get_object_or_404(Publisher, pk=pk)

    if request.method == "POST":
        # Remove user from publisher based on role
        if request.user.role == "journalist":
            publisher.journalists.remove(request.user)
            messages.info(request, f"You left {publisher.name}")
        elif request.user.role == "editor":
            publisher.editors.remove(request.user)
            messages.info(request, f"You left {publisher.name}")

        return redirect("publisher_list")

    return render(
        request, "news_app/publisher_leave_confirm.html", {"publisher": publisher}
    )
