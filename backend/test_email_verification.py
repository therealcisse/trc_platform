#!/usr/bin/env python
"""Test script for email verification endpoints."""
import json
from django.test import TestCase, Client
from django.urls import reverse
from customers.models import User, InviteCode
from django.core import mail
from django.core.signing import TimestampSigner
from django.utils import timezone


class EmailVerificationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an invite code for registration
        self.invite_code = InviteCode.objects.create(
            code=InviteCode.generate_code(),
            is_active=True
        )
        
    def test_registration_sends_email(self):
        """Test that registration sends a verification email with HTML content."""
        data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "inviteCode": self.invite_code.code
        }
        
        response = self.client.post(
            reverse("register"),
            data=json.dumps(data),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 202)
        
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        
        # Check the email details
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, "Verify Your Email Address")
        self.assertEqual(sent_email.to, ["testuser@example.com"])
        
        # Check that HTML content is present
        self.assertIsNotNone(sent_email.alternatives)
        html_content = sent_email.alternatives[0][0]
        self.assertIn("Welcome! Verify Your Email Address", html_content)
        self.assertIn("Verify Email Address", html_content)
        self.assertIn("This verification link will expire in 24 hours", html_content)
        
    def test_resend_verification_email(self):
        """Test that resend verification email endpoint works correctly."""
        # First create a user
        user = User.objects.create_user(
            email="testuser2@example.com",
            password="TestPassword123!"
        )
        
        # Login
        self.client.force_login(user)
        
        # Request resend verification
        response = self.client.post(reverse("resend-verification"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["detail"], "Verification email sent successfully")
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, "Verify Your Email Address")
        self.assertEqual(sent_email.to, ["testuser2@example.com"])
        
        # Check HTML content
        self.assertIsNotNone(sent_email.alternatives)
        html_content = sent_email.alternatives[0][0]
        self.assertIn("Verify Your Email Address", html_content)
        self.assertIn("Thank you for signing up!", html_content)
        
    def test_resend_verification_fails_if_already_verified(self):
        """Test that resend fails if email is already verified."""
        # Create a verified user
        user = User.objects.create_user(
            email="testuser3@example.com",
            password="TestPassword123!",
            email_verified_at=timezone.now()
        )
        
        # Login
        self.client.force_login(user)
        
        # Try to resend verification
        response = self.client.post(reverse("resend-verification"))
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["code"], "email_already_verified")
        
    def test_verification_link_works(self):
        """Test that the verification link actually verifies the email."""
        # Create an unverified user
        user = User.objects.create_user(
            email="testuser4@example.com",
            password="TestPassword123!"
        )
        
        # Generate a verification token
        signer = TimestampSigner()
        token = signer.sign(user.email)
        
        # Verify email
        response = self.client.get(
            reverse("verify-email") + f"?token={token}"
        )
        
        self.assertEqual(response.status_code, 204)
        
        # Check that user is now verified
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertIsNotNone(user.email_verified_at)


if __name__ == "__main__":
    import sys
    import os
    import django
    
    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    
    # Run tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(["test_email_verification"])
    sys.exit(bool(failures))
