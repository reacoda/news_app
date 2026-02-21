# from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from django.contrib.auth.models import Group

from .models import CustomUser, Article, Publisher
from .utils import assign_user_to_group


class ArticleAPITest(APITestCase):
    """
    Tests for Article REST API endpoints.
    Tests authentication and authorization
    for all three user roles.
    """

    def setUp(self):
        """
        Runs BEFORE every single test!
        Creates fresh test data each time.
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
        Helper function to get JWT token.
        Avoids repeating token code in every test!
        """
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url, {"username": username, "password": password}, format="json"
        )
        return response.data["access"]

    def auth_header(self, token):
        """
        Helper function to create
        Authorization header.
        """
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # ==========================================
    # AUTHENTICATION TESTS
    # ==========================================

    def test_unauthenticated_cannot_access_api(self):
        """
        Test that unauthenticated users
        cannot access API endpoints.
        Expected: 401 Unauthorized
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
        Test that readers CAN view articles.
        Expected: 200 OK
        """
        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_article_list")
        response = self.client.get(url, **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("Reader can view articles!")

    def test_reader_cannot_create_article(self):
        """
        Test that readers CANNOT create articles.
        Expected: 403 Forbidden
        """
        token = self.get_token("test_reader", "testpass123")
        url = reverse("api_article_list")
        data = {"title": "Reader Article Attempt", "content": "Readers cannot create!"}
        response = self.client.post(url, data, format="json", **self.auth_header(token))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("Reader blocked from creating!")

    def test_reader_subscribed_articles(self):
        """
        Test reader only gets articles from
        subscribed journalists/publishers.
        Expected: 200 OK + correct articles
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
        Test that journalists CAN create articles.
        Expected: 201 Created
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
        Test journalist can update their article.
        Expected: 200 OK
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
        Test editor can approve articles.
        Also tests email and twitter are called!
        Expected: 200 OK + approved=True
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
        Test editor can delete articles.
        Expected: 204 No Content
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
        Test reader cannot create newsletter.
        Expected: 403 Forbidden
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
