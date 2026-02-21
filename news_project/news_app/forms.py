from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Article, Newsletter


class UserRegistrationForm(UserCreationForm):
    """
    Registration for new users.
    Extends Django's built-in UserCreationForm
    UserCreationForm already handles:
    - Password matching validation
    - Password strength validation
    - Username uniqueness validation
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
        Custom validation for email field
        Checks if email is already registered
        """

        email = self.cleaned_data.get("email")

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered!")
        return email


class ArticleForm(forms.ModelForm):
    """
    Form for journalists to create/edit articles
    Only shows fields journalist should fill manually
    Author, created_at, approved are handled automatically
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
    Form for journalists to create/edit newsletters
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
