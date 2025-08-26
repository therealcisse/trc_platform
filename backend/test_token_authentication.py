"""
Test suite for API token authentication for the image solver endpoint.

This test suite verifies all security requirements for token authentication:
1. Token format validation
2. Token status checks (not revoked)
3. User status checks (active, email verified)
4. Proper authentication flow
"""

import io
from datetime import UTC, datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from customers.models import ApiToken

User = get_user_model()


@override_settings(SAVE_REQUEST_IMAGES=False)
class TokenAuthenticationTestCase(TestCase):
    """Test API token authentication for the solver endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.solve_url = reverse("solve")

        # Create a verified user
        self.verified_user = User.objects.create_user(
            email="verified@example.com",
            password="testpass123",
        )
        self.verified_user.email_verified_at = datetime.now(UTC)
        self.verified_user.save()

        # Create an unverified user
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com",
            password="testpass123",
        )

        # Create an inactive user
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="testpass123",
        )
        self.inactive_user.email_verified_at = datetime.now(UTC)
        self.inactive_user.is_active = False
        self.inactive_user.save()

        # Generate tokens
        self.verified_token, _, _ = ApiToken.generate_token()
        self.verified_api_token = ApiToken.objects.create(
            user=self.verified_user,
            name="Test Token",
            token_prefix=self.verified_token[:12],
            token_hash=ApiToken.generate_token()[2],  # Generate a new hash
        )
        # Manually set the correct hash for our known token
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        self.verified_api_token.token_hash = ph.hash(self.verified_token)
        self.verified_api_token.save()

        # Token for unverified user
        self.unverified_token, _, _ = ApiToken.generate_token()
        self.unverified_api_token = ApiToken.objects.create(
            user=self.unverified_user,
            name="Unverified Token",
            token_prefix=self.unverified_token[:12],
            token_hash=ApiToken.generate_token()[2],
        )
        ph = PasswordHasher()
        self.unverified_api_token.token_hash = ph.hash(self.unverified_token)
        self.unverified_api_token.save()

        # Token for inactive user
        self.inactive_token, _, _ = ApiToken.generate_token()
        self.inactive_api_token = ApiToken.objects.create(
            user=self.inactive_user,
            name="Inactive Token",
            token_prefix=self.inactive_token[:12],
            token_hash=ApiToken.generate_token()[2],
        )
        ph = PasswordHasher()
        self.inactive_api_token.token_hash = ph.hash(self.inactive_token)
        self.inactive_api_token.save()

        # Create a revoked token
        self.revoked_token, _, _ = ApiToken.generate_token()
        self.revoked_api_token = ApiToken.objects.create(
            user=self.verified_user,
            name="Revoked Token",
            token_prefix=self.revoked_token[:12],
            token_hash=ApiToken.generate_token()[2],
        )
        ph = PasswordHasher()
        self.revoked_api_token.token_hash = ph.hash(self.revoked_token)
        self.revoked_api_token.revoked_at = datetime.now(UTC)
        self.revoked_api_token.save()

        # Create test image
        self.test_image = SimpleUploadedFile(
            name="test.jpg",
            content=b"fake_image_content",
            content_type="image/jpeg"
        )

    @patch("core.views.openai_client.solve_image")
    def test_valid_token_authentication(self, mock_solve):
        """Test successful authentication with valid token."""
        mock_solve.return_value = {
            "result": "42",
            "model": "gpt-4-vision",
        }

        # Make request with valid token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.verified_token}")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], "42")

        # Verify token's last_used_at was updated
        self.verified_api_token.refresh_from_db()
        self.assertIsNotNone(self.verified_api_token.last_used_at)

    def test_missing_token(self):
        """Test request without token is rejected."""
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_token_format(self):
        """Test request with invalid token format is rejected."""
        # Token without tok_ prefix
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_format")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_existent_token(self):
        """Test request with non-existent token is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok_nonexistent123456")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_revoked_token(self):
        """Test request with revoked token is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.revoked_token}")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unverified_email(self):
        """Test request with token from unverified user is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.unverified_token}")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_user(self):
        """Test request with token from inactive user is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.inactive_token}")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_authentication_not_allowed(self):
        """Test that session authentication is not allowed for solver endpoint."""
        # Login via session
        self.client.force_authenticate(user=self.verified_user)

        # Try to access solver without token (only session)
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Should be rejected because IsTokenAuthenticated requires token auth
        # Returns 403 when permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_wrong_hash(self):
        """Test request with token that has wrong hash is rejected."""
        # Create a token with wrong hash - store a valid Argon2 hash format but for different content
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        wrong_token = "tok_wronghash1234567890"
        wrong_api_token = ApiToken.objects.create(
            user=self.verified_user,
            name="Wrong Hash Token",
            token_prefix=wrong_token[:12],
            token_hash=ph.hash("different_token"),  # Hash of a different token
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {wrong_token}")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        # Returns 403 when permission check fails (token validation failed)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("core.views.openai_client.solve_image")
    def test_request_logging_with_token(self, mock_solve):
        """Test that requests are properly logged with token information."""
        mock_solve.return_value = {
            "result": "x = 5",
            "model": "gpt-4-vision",
        }

        from usage.models import RequestLog

        # Make request with valid token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.verified_token}")
        response = self.client.post(
            self.solve_url,
            {"file": self.test_image},
            format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that request was logged with token
        log = RequestLog.objects.filter(user=self.verified_user).last()
        self.assertIsNotNone(log)
        self.assertEqual(log.token.id, self.verified_api_token.id)
        self.assertEqual(log.service, "core.image_solve")
        self.assertEqual(log.status, "success")
        self.assertEqual(log.result, "x = 5")

    @patch("core.views.openai_client.solve_image")
    def test_binary_upload_with_token(self, mock_solve):
        """Test binary upload with token authentication."""
        mock_solve.return_value = {
            "result": "y = 10",
            "model": "gpt-4-vision",
            "return_dict": True,
        }

        # Send raw binary data as application/octet-stream
        # The view should accept this format
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.verified_token}")
        response = self.client.post(
            self.solve_url,
            data=b"fake_image_binary_data",
            content_type="application/octet-stream"
        )

        # The current implementation with application/octet-stream requires
        # a Content-Disposition header with filename, which we're not providing
        # This test verifies that authentication works properly even when the request fails
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing filename", response.data["detail"])

    def test_token_prefix_uniqueness(self):
        """Test that token prefixes are unique."""
        # Generate many tokens and check prefix uniqueness
        prefixes = set()
        for _ in range(100):
            token, prefix, _ = ApiToken.generate_token()
            self.assertEqual(len(prefix), 12)
            self.assertTrue(prefix.startswith("tok_"))
            prefixes.add(prefix)

        # All prefixes should be unique
        self.assertEqual(len(prefixes), 100)

    def test_authorization_header_variations(self):
        """Test various Authorization header formats."""
        test_cases = [
            ("bearer " + self.verified_token, False),  # lowercase bearer
            ("BEARER " + self.verified_token, False),  # uppercase BEARER
            ("Bearer  " + self.verified_token, False),  # extra space
            (" Bearer " + self.verified_token, False),  # leading space
            ("Basic " + self.verified_token, False),    # wrong auth type
            (self.verified_token, False),               # no Bearer prefix
            ("Bearer " + self.verified_token, True),    # correct format
        ]

        for auth_header, should_succeed in test_cases:
            with self.subTest(auth_header=auth_header):
                self.client.credentials(HTTP_AUTHORIZATION=auth_header)
                response = self.client.post(
                    self.solve_url,
                    {"file": self.test_image},
                    format="multipart"
                )

                if should_succeed:
                    with patch("core.views.openai_client.solve_image") as mock_solve:
                        mock_solve.return_value = {"result": "42", "model": "gpt-4"}
                        self.client.credentials(HTTP_AUTHORIZATION=auth_header)
                        response = self.client.post(
                            self.solve_url,
                            {"file": self.test_image},
                            format="multipart"
                        )
                        self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    # Returns 403 when permission check fails
                    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TokenManagementTestCase(TestCase):
    """Test API token management endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create verified user
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123"
        )
        self.user.email_verified_at = datetime.now(UTC)
        self.user.save()

        # Create unverified user
        self.unverified_user = User.objects.create_user(
            email="unverified@example.com",
            password="testpass123"
        )

    def test_create_token_requires_verified_email(self):
        """Test that creating a token requires verified email."""
        # Login as unverified user
        self.client.force_authenticate(user=self.unverified_user)

        response = self.client.post(
            "/api/customers/tokens",
            {"name": "My Token"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_token_success(self):
        """Test successful token creation."""
        # Login as verified user
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/customers/tokens",
            {"name": "My API Token"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token_once", response.data)
        self.assertIn("token_prefix", response.data)
        self.assertTrue(response.data["token_once"].startswith("tok_"))

        # Verify token was created in database
        token = ApiToken.objects.get(user=self.user, name="My API Token")
        self.assertIsNotNone(token)
        self.assertIsNone(token.revoked_at)

    def test_list_tokens(self):
        """Test listing user's tokens."""
        # Create some tokens
        token1 = ApiToken.objects.create(
            user=self.user,
            name="Token 1",
            token_prefix="tok_11111111",
            token_hash="hash1"
        )
        token2 = ApiToken.objects.create(
            user=self.user,
            name="Token 2",
            token_prefix="tok_22222222",
            token_hash="hash2"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/customers/tokens")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Should not include token_hash or full token
        for token_data in response.data:
            self.assertNotIn("token_hash", token_data)
            self.assertNotIn("token_once", token_data)

    def test_revoke_token(self):
        """Test revoking a token."""
        token = ApiToken.objects.create(
            user=self.user,
            name="Token to Revoke",
            token_prefix="tok_revoke12",
            token_hash="hash"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/customers/tokens/{token.id}")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify token was revoked, not deleted
        token.refresh_from_db()
        self.assertIsNotNone(token.revoked_at)
        self.assertTrue(token.is_revoked)

    def test_cannot_revoke_other_users_token(self):
        """Test that users cannot revoke other users' tokens."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123"
        )
        other_user.email_verified_at = datetime.now(UTC)
        other_user.save()

        other_token = ApiToken.objects.create(
            user=other_user,
            name="Other User Token",
            token_prefix="tok_other123",
            token_hash="hash"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/customers/tokens/{other_token.id}")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify token was not revoked
        other_token.refresh_from_db()
        self.assertIsNone(other_token.revoked_at)
