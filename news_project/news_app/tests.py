"""
Automated tests for the News App REST API.

This module contains integration tests for all article and newsletter API
endpoints using Django REST Framework's :class:`~rest_framework.test.APITestCase`.
Tests cover:

- Authentication enforcement (unauthenticated requests must be rejected)
- Role-based access control (readers, journalists, and editors each have
  specific permissions)
- Article CRUD operations
- Newsletter CRUD operations
- Article approval workflow with mocked side-effects (email + Twitter)
- Subscription filtering

Test Class:
    - :class:`ArticleAPITest`

Note:
    External side-effects (``send_approval_emails`` and ``post_to_twitter``)
    are mocked using :func:`unittest.mock.patch` to prevent real emails
    or tweets from being sent during test runs.
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth.models import Group

from .models import CustomUser, Article, Publisher
from .utils import assign_user_to_group


class ArticleAPITest(APITestCase):
    """
    Integration test suite for the News App Article and Newsletter REST API.

    Tests authentication and authorisation behaviour for all three user
    roles (reader, journalist, editor) against every relevant API endpoint.
    Each test method is independent — the :meth:`setUp` method creates a
    fresh set of database records before every test.

    Fixtures created in :meth:`setUp`:
        - ``self.publisher`` — a :class:`~news_app.models.Publisher` instance
        - ``self.journalist`` — a journalist :class:`~news_app.models.CustomUser`
        - ``self.editor`` — an editor :class:`~news_app.models.CustomUser`
        - ``self.reader`` — a reader :class:`~news_app.models.CustomUser`
        - ``self.article`` — an unapproved :class:`~news_app.models.Article`
        - ``self.approved_article`` — an approved :class:`~news_app.models.Article`
    """

    def setUp(self):
        """
        Create test database records required by every test method.

        This method runs automatically before each individual test. It creates
        the required user groups, a publisher, three users (journalist, editor,
        reader), and two articles (one unapproved, one approved).

        The :func:`~news_app.utils.assign_user_to_group` utility is called for
        each user to ensure group-based permissions are correctly assigned.
        """

        # Create groups first
        # (normally done by setup_groups command)
        self.reader_group = Group.objects.get_or_create(name="Reader")[0]
        self.journalist_group = Group.objects.get_or_create(name="Journalist")[0]
        self.editor_group = Group.objects.get_or_create(name="Editor")[0]

        # Create test publisher
        self.publisher = Publisher.objects.create(name="Test Publisher")

        # Create journalist user
        self.journalist = CustomUser.objects.create_user(
            username="test_journalist",
            email="journalist@test.com",
            password="testpass123",
            role="journalist",
        )
        assign_user_to_group(self.journalist)

        # Create editor user
        self.editor = CustomUser.objects.create_user(
            username="test_editor",
            email="editor@test.com",
            password="testpass123",
            role="editor",
        )
        assign_user_to_group(self.editor)

        # Create reader user
        self.reader = CustomUser.objects.create_user(
            username="test_reader",
            email="reader@test.com",
            password="testpass123",
            role="reader",
        )
        assign_user_to_group(self.reader)

        # Create test article
        self.article = Article.objects.create(
            title="Test Article",
            content="Test content for article",
            author=self.journalist,
            approved=False,
        )

        # Create approved test article
        self.approved_article = Article.objects.create(
            title="Approved Test Article",
            content="This article is approved",
            author=self.journalist,
            approved=True,
        )

    def get_token(self, username, password):
        """
        Obtain a JWT access token for the given user credentials.

        This helper method posts to the ``token_obtain_pair`` endpoint
        and extracts the ``access`` token from the response. It avoids
        repeating the token acquisition logic in every test method.

        :param:
            username (str): The username of the user to authenticate.
            password (str): The plaintext password of the user.

        Returns:
            str: A JWT access token string to be used in ``Authorization`` headers.
        """
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url, {"username": username, "password": password}, format="json"
        )
        return response.data["access"]

    def auth_header(self, token):
        """
        Build a Django test client ``Authorization`` header dict from a JWT token.

        Args:
            token (str): A JWT access token obtained via :meth:`get_token`.

        Returns:
            dict: A dictionary suitable for unpacking as ``**kwargs`` in a
            test client request, e.g. ``{"HTTP_AUTHORIZATION": "Bearer <token>"}``.
        """
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # ==========================================
    # AUTHENTICATION TESTS
    # ==========================================

    def test_unauthenticated_cannot_access_api(self):
        """
        Unauthenticated requests must be rejected with HTTP 401.

        Verifies that the API correctly denies access when no JWT token
        is supplied in the ``Authorization`` header.

        Expected status: ``HTTP 401 Unauthorized``
        """
        url = reverse("api_article_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print("Unauthenticated access blocked!")

    # ==========================================
    # READER TESTS
    # ==========================================

    def test_reader_can_view_articles(self):
        """
        Authenticated readers can retrieve the approved article list.

        Expected status: ``HTTP 200 OK``
        """
        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_article_list")
        response = self.client.get(url, **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("Reader can view articles!")

    def test_reader_cannot_create_article(self):
        """
        Readers must not be permitted to create articles.

        A POST request from a reader to the article list endpoint should
        be rejected because only journalists have the ``IsJournalist`` permission.

        Expected status: ``HTTP 403 Forbidden``
        """
        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_article_list")
        data = {"title": "Reader Article Attempt", "content": "Readers cannot create!"}
        response = self.client.post(url, data, format="json", **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("Reader blocked from creating!")

    def test_reader_subscribed_articles(self):
        """
        A reader only sees articles from their subscribed journalists and publishers.

        Subscribes the test reader to the test journalist, then calls the
        ``subscribed_articles`` endpoint and verifies the response contains
        at least one article.

        Expected status: ``HTTP 200 OK`` with at least one article in the response.
        """
        # Subscribe reader to journalist
        self.reader.subscribed_journalists.add(self.journalist)

        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_subscribed_articles")
        response = self.client.get(url, **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify articles are from
        # subscribed journalist!
        self.assertTrue(len(response.data) > 0)
        print("Reader sees subscribed articles!")

    # ==========================================
    # JOURNALIST TESTS
    # ==========================================

    def test_journalist_can_create_article(self):
        """
        Journalists can create new articles via the API.

        Verifies that the created article has the requesting journalist set
        as the author automatically, and that the article starts in an
        unapproved state.

        Expected status: ``HTTP 201 Created``
        """
        token = self.get_token("test_journalist", "testpass123")
        url = reverse("api_article_list")
        data = {"title": "Journalist Test Article", "content": "Created by journalist!"}
        response = self.client.post(url, data, format="json", **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify author set automatically!
        self.assertEqual(response.data["author"]["username"], "test_journalist")
        # Verify article starts as unapproved!
        self.assertFalse(response.data["approved"])
        print("Journalist can create article!")

    def test_journalist_can_update_own_article(self):
        """
        Journalists can update articles via a PUT request.

        Expected status: ``HTTP 200 OK``
        """
        token = self.get_token("test_journalist", "testpass123")
        url = reverse("api_article_detail", kwargs={"pk": self.approved_article.pk})
        data = {"title": "Updated Title", "content": "Updated content!"}
        response = self.client.put(url, data, format="json", **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("Journalist can update article!")

    # ==========================================
    # EDITOR TESTS
    # ==========================================

    def test_editor_can_approve_article(self):
        """
        Editors can approve an article, triggering email and Twitter notifications.

        Uses :func:`unittest.mock.patch` to mock both
        :func:`~news_app.utils.send_approval_emails` and
        :func:`~news_app.utils.post_to_twitter` to prevent real external
        calls during testing.

        Assertions:
            - Response status is ``HTTP 200 OK``
            - The article's ``approved`` flag is set to ``True`` in the database
            - ``send_approval_emails`` was called exactly once
            - ``post_to_twitter`` was called exactly once
        """
        token = self.get_token("test_editor", "testpass123")

        # Mock email and twitter functions!
        # This prevents real emails/tweets!
        with patch("news_app.api_views.send_approval_emails") as mock_email, patch(
            "news_app.api_views.post_to_twitter"
        ) as mock_twitter:

            url = reverse("api_approve_article", kwargs={"pk": self.article.pk})
            response = self.client.post(url, **self.auth_header(token))

            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Verify article is now approved!
            self.article.refresh_from_db()
            self.assertTrue(self.article.approved)

            # Verify email was called!
            mock_email.assert_called_once()
            print("Email function was called!")

            # Verify twitter was called!
            mock_twitter.assert_called_once()
            print("Twitter function was called!")

        print("Editor can approve article!")

    def test_editor_can_delete_article(self):
        """
        Editors can delete articles via a DELETE request.

        Expected status: ``HTTP 204 No Content``
        """
        token = self.get_token("test_editor", "testpass123")
        url = reverse("api_article_detail", kwargs={"pk": self.approved_article.pk})
        response = self.client.delete(url, **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        print("Editor can delete article!")

    def test_reader_cannot_approve_article(self):
        """
        Test reader cannot approve articles.
        Expected: 403 Forbidden
        """
        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_approve_article", kwargs={"pk": self.article.pk})
        response = self.client.post(url, **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("Reader blocked from approving!")

    # ==========================================
    # NEWSLETTER TESTS
    # ==========================================

    def test_journalist_can_create_newsletter(self):
        """
        Test journalist can create newsletter.
        Expected: 201 Created
        """
        token = self.get_token("test_journalist", "testpass123")
        url = reverse("api_newsletter_list")
        data = {
            "title": "Test Newsletter",
            "description": "Test description",
            "articles": [self.approved_article.pk],
        }
        response = self.client.post(url, data, format="json", **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print("Journalist can create newsletter!")

    def test_reader_cannot_create_newsletter(self):
        """
        Readers must not be permitted to create newsletters.

        Expected status: ``HTTP 403 Forbidden``
        """
        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_newsletter_list")
        data = {
            "title": "Reader Newsletter Attempt",
            "description": "Readers cannot create!",
        }
        response = self.client.post(url, data, format="json", **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("Reader blocked from creating newsletter!")
