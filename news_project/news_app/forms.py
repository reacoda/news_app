"""
Django form definitions for the News App.

This module contains all form classes used for user input across the
application, including user registration, article creation/editing,
and newsletter creation/editing.

Forms:
    - :class:`UserRegistrationForm` — handles new user sign-up
    - :class:`ArticleForm` — used by journalists to write articles
    - :class:`NewsletterForm` — used by journalists to curate newsletters
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Article, Newsletter


class UserRegistrationForm(UserCreationForm):
    """
    Form for registering a new user account.

    Extends Django's built-in :class:`~django.contrib.auth.forms.UserCreationForm`
    to add ``email`` and ``role`` fields required by the
    :class:`~news_app.models.CustomUser` model.

    The parent class automatically handles:
        - Password confirmation matching (``password1`` vs ``password2``)
        - Password strength validation
        - Username uniqueness validation

    Attributes:
        email (EmailField): Required field for the user's email address.
            Validated for format and uniqueness via :meth:`clean_email`.
        role (ChoiceField): Required field for selecting the user's role.
            Choices are drawn from :attr:`~news_app.models.CustomUser.ROLE_CHOICES`.

    Example:
        Typical usage in a registration view::

            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.role = form.cleaned_data["role"]
                user.save()
    """

    # Add the extra fields we need: email and role
    email = forms.EmailField(
        required=True, help_text="Required. Enter a valid email address."
    )

    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES, required=True, help_text="Select your role"
    )

    class Meta:
        model = CustomUser
        # Fields that appear on registration form
        fields = [
            "username",
            "email",
            "role",
            "password1",  # password1 & password2 are
            "password2",  # from UserCreationForm
        ]

    def clean_email(self):
        """
        Validate that the submitted email address has not already been registered.

        This method is called automatically by Django's form validation pipeline
        when ``form.is_valid()`` is invoked.

        Raises:
            forms.ValidationError: If a :class:`~news_app.models.CustomUser`
                with the given email address already exists in the database.

        Returns:
            str: The cleaned, validated email address string.
        """

        email = self.cleaned_data.get("email")

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered!")
        return email


class ArticleForm(forms.ModelForm):
    """
    Form for creating and editing a news article.

    Intended for use by journalists. Only exposes the fields that a journalist
    should fill in manually — ``title``, ``content``, and ``publisher``.
    The ``author``, ``created_at``, and ``approved`` fields are set
    automatically by the view and are not shown to the user.

    Attributes:
        Meta.model (Article): The model this form is bound to.
        Meta.fields (list): The subset of model fields exposed in the form.
        Meta.widgets (dict): Custom Bootstrap-styled widget configurations
            for each field.

    Example:
        Creating a new article in a view::

            form = ArticleForm(request.POST)
            if form.is_valid():
                article = form.save(commit=False)
                article.author = request.user
                article.save()
    """

    class Meta:
        model = Article
        # Only manual fields shown to journalist
        fields = ["title", "content", "publisher"]

        # Make form fields more presentable
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter article title..."}
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Write your article here...",
                    "rows": 10,
                }
            ),
            "publisher": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class NewsletterForm(forms.ModelForm):
    """
    Form for creating and editing a newsletter.

    Intended for use by journalists. Allows a journalist to provide a
    ``title``, ``description``, and select which approved ``articles`` to
    include. The ``author`` and ``created_at`` fields are set automatically
    by the view.

    Attributes:
        Meta.model (Newsletter): The model this form is bound to.
        Meta.fields (list): The subset of model fields exposed in the form.
        Meta.widgets (dict): Custom widget configurations for each field,
            including a :class:`~django.forms.CheckboxSelectMultiple` widget
            for the articles ManyToMany relationship.

    Example:
        Creating a newsletter in a view::

            form = NewsletterForm(request.POST)
            if form.is_valid():
                newsletter = form.save(commit=False)
                newsletter.author = request.user
                newsletter.save()
                form.save_m2m()  # Required to save ManyToMany articles field
    """

    class Meta:
        model = Newsletter
        fields = ["title", "description", "articles"]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Newsletter title..."}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe your newsletter...",
                    "rows": 5,
                }
            ),
            "articles": forms.CheckboxSelectMultiple(),
        }
