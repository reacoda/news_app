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
    Landing page.
    Redirects logged in users to dashboard.
    Shows landing page to visitors.
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
    Creates user, assigns role and group
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
    Uses Django's built-in LoginView.
    Need to customize the template
    Django will handle all the login logic
    """

    template_name = "news_app/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Redirect to dashboard after login
        """
        return "/dashboard"


def logout_view(request):
    """
    Logs user out and redirects to login
    """
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect("login")


# Dashboard View


@login_required
def dashboard_view(request):
    """
    Role-based dashboard
    Shows different content based on user role
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
    Shows all the approved articles to everyone
    """
    # Only get approved articles
    articles = Article.objects.filter(approved=True).order_by("-created_at")

    return render(request, "news_app/article_list.html", {"articles": articles})


def article_detail_view(request, pk):
    """
    Shows single article detail.
    Returns 404 if article not found.
    """
    # get_object_or_404 handles wrong IDs
    article = get_object_or_404(Article, pk=pk, approved=True)

    return render(request, "news_app/article_detail.html", {"article": article})


@login_required
@permission_required("news_app.add_article", raise_exception=True)
def create_article_view(request):
    """
    Allows journalists to create articles
    Requires login and add_article permission
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
@permission_required(
    'news_app.change_article',
    raise_exception=True
)
def edit_article_view(request, pk):
    """
    Allows journalists/editors to edit articles.
    """
    article = get_object_or_404(Article, pk=pk)
    
    # Journalist can only edit OWN articles
    if request.user.role == 'journalist':
        if article.author != request.user:
            messages.error(
                request,
                'You can only edit your own articles!'
            )
            return redirect('dashboard')
    
    if request.method == 'POST':
        form = ArticleForm(
            request.POST,
            instance=article
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Article updated successfully!'
            )
            # Redirect to dashboard
            return redirect('dashboard')
    else:
        form = ArticleForm(instance=article)
    
    return render(
        request,
        'news_app/article_form.html',
        {
            'form': form,
            'action': 'Edit'
        }
    )


@login_required
@permission_required("news_app.can_approve_article", raise_exception=True)
def approve_article_view(request, pk):
    """
    Allows editors to approve articles
    When approved:
    1. Sends email to subscribers
    2. Posts to X (Twitter)
    Both handled here in view (no signals)
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
    Allows editors/journalists to delete articles.
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
    Shows all newsletters to everyone.
    """
    newsletters = Newsletter.objects.all().order_by("-created_at")

    return render(
        request, "news_app/newsletter_list.html", {"newsletters": newsletters}
    )


def newsletter_detail_view(request, pk):
    """
    Shows single newsletter detail.
    Returns 404 if not found.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    return render(
        request, "news_app/newsletter_detail.html", {"newsletter": newsletter}
    )


@login_required
@permission_required("news_app.add_newsletter", raise_exception=True)
def create_newsletter_view(request):
    """
    Allows journalists to create newsletters.
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
    Allows journalists/editors to
    edit newsletters.
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
    Allows journalists/editors to
    delete newsletters.
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
    Shows reader's current subscriptions.
    Allows managing subscriptions.
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
    Toggles subscription to a publisher.
    If subscribed - unsubscribe
    If not subscribed - subscribe
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
    Toggles subscription to a journalist.
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
    Shows all publishers.
    """
    publishers = Publisher.objects.all().order_by('name')
    
    return render(
        request,
        'news_app/publisher_list.html',
        {'publishers': publishers}
    )


@login_required
# @permission_required(
#     'news_app.add_publisher',
#     raise_exception=True
# )
def create_publisher_view(request):
    """
    Allows creating new publishers.
    Only superusers or staff can create publishers.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if name:
            publisher = Publisher.objects.create(
                name=name
            )
            messages.success(
                request,
                f'Publisher "{name}" created successfully!'
            )
            return redirect('publisher_list')
        else:
            messages.error(
                request,
                'Publisher name is required!'
            )
    
    return render(
        request,
        'news_app/publisher_form.html',
        {'action': 'Create'}
    )


@login_required
def join_publisher_view(request, pk):
    """
    Allows journalists/editors to join a publisher.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    
    if request.method == 'POST':
        # Add user to publisher based on role
        if request.user.role == 'journalist':
            publisher.journalists.add(request.user)
            messages.success(
                request,
                f'You joined {publisher.name} as a journalist!'
            )
        elif request.user.role == 'editor':
            publisher.editors.add(request.user)
            messages.success(
                request,
                f'You joined {publisher.name} as an editor!'
            )
        else:
            messages.error(
                request,
                'Only journalists and editors can join publishers!'
            )
        
        return redirect('publisher_list')
    
    return render(
        request,
        'news_app/publisher_join_confirm.html',
        {'publisher': publisher}
    )


@login_required
def leave_publisher_view(request, pk):
    """
    Allows journalists/editors to leave a publisher.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    
    if request.method == 'POST':
        # Remove user from publisher based on role
        if request.user.role == 'journalist':
            publisher.journalists.remove(request.user)
            messages.info(
                request,
                f'You left {publisher.name}'
            )
        elif request.user.role == 'editor':
            publisher.editors.remove(request.user)
            messages.info(
                request,
                f'You left {publisher.name}'
            )
        
        return redirect('publisher_list')
    
    return render(
        request,
        'news_app/publisher_leave_confirm.html',
        {'publisher': publisher}
    )
