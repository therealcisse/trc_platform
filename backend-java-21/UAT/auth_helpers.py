#!/usr/bin/env python3
"""
Auth Helpers for TRC Platform UAT Testing
Authentication-specific validation and utility functions.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime

from uat_framework import DatabaseHelper, HTTPClient, Colors, print_info, print_error, print_success, TestStep


class AuthHelper:
    """Authentication-specific operations and validation"""

    def __init__(self, db_helper: DatabaseHelper, http_client: HTTPClient):
        self.db_helper = db_helper
        self.http_client = http_client

    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False

        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return bool(email_pattern.match(email))

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength requirements"""
        result = {
            "is_valid": True,
            "errors": [],
            "min_length": 8,
            "has_upper": False,
            "has_lower": False,
            "has_digit": False,
            "has_special": False
        }

        if len(password) < result["min_length"]:
            result["errors"].append(f"Password must be at least {result['min_length']} characters long")
            result["is_valid"] = False

        if re.search(r'[A-Z]', password):
            result["has_upper"] = True
        else:
            result["errors"].append("Password must contain at least one uppercase letter")
            result["is_valid"] = False

        if re.search(r'[a-z]', password):
            result["has_lower"] = True
        else:
            result["errors"].append("Password must contain at least one lowercase letter")
            result["is_valid"] = False

        if re.search(r'\d', password):
            result["has_digit"] = True
        else:
            result["errors"].append("Password must contain at least one digit")
            result["is_valid"] = False

        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result["has_special"] = True
        else:
            result["errors"].append("Password must contain at least one special character")
            result["is_valid"] = False

        return result

    def create_registration_data(self, email: str, password: str, invite_code: str) -> Dict[str, Any]:
        """Create user registration request data"""
        return {
            "email": email,
            "password": password,
            "confirmPassword": password,
            "inviteCode": invite_code,
            "userAcceptedTerms": True,
            "userAcceptedDisclaimer": True,
        }

    def create_login_data(self, email: str, password: str) -> Dict[str, Any]:
        """Create login request data"""
        return {
            "email": email,
            "password": password
        }

    def verify_user_registration(self, email: str) -> bool:
        """Verify user was registered successfully"""
        return self.db_helper.verify_user_exists(email)

    def verify_user_email_verification(self, email: str) -> bool:
        """Verify user email was verified"""
        return self.db_helper.verify_email_verified(email)

    def validate_invite_code_format(self, code: str) -> bool:
        """Validate invite code format"""
        if not code or not isinstance(code, str):
            return False

        # Basic invite code format validation
        return len(code) >= 4 and code.replace('-', '').replace('_', '').isalnum()

    def create_invite_code_data(self, max_uses: int = 1, expires_in_days: int = 30) -> Dict[str, Any]:
        """Create invite code request data"""
        return {
            "maxUses": max_uses,
            "expiresInDays": expires_in_days
        }

    def verify_invite_code_created(self, code: str) -> bool:
        """Verify invite code was created"""
        return self.db_helper.verify_invite_code_exists(code, active_only=True)

    def check_invite_code_usage(self, code: str) -> Optional[Dict[str, Any]]:
        """Check if invite code has been used"""
        return self.db_helper.check_invite_code_usage(code)

    def create_password_change_data(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Create password change request data"""
        return {
            "currentPassword": current_password,
            "newPassword": new_password
        }

    def create_email_verification_request(self, email: str) -> Dict[str, Any]:
        """Create email verification request data"""
        return {
            "email": email
        }

    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token format and structure"""
        result = {
            "is_valid": False,
            "errors": [],
            "header": None,
            "payload": None,
            "signature": None
        }

        if not token or not isinstance(token, str):
            result["errors"].append("Token must be a non-empty string")
            return result

        parts = token.split('.')
        if len(parts) != 3:
            result["errors"].append(f"Invalid JWT format. Expected 3 parts, got {len(parts)}")
            return result

        result["header"] = parts[0]
        result["payload"] = parts[1]
        result["signature"] = parts[2]

        # Basic format validation (base64url encoding)
        base64url_pattern = re.compile(r'^[A-Za-z0-9_-]*$')

        for part_name, part in [("header", parts[0]), ("payload", parts[1]), ("signature", parts[2])]:
            if not base64url_pattern.match(part):
                result["errors"].append(f"Invalid base64url format in {part_name}")
                return result

        result["is_valid"] = True
        return result

    def extract_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token payload"""
        try:
            import jwt
            import json
            from base64 import urlsafe_b64decode

            # Decode payload (middle part of JWT)
            payload_b64 = token.split('.')[1]

            # Add padding if needed
            padding = '=' * (4 - len(payload_b64) % 4)
            payload_json = urlsafe_b64decode(payload_b64 + padding).decode('utf-8')

            payload = json.loads(payload_json)

            # Extract user-related fields
            user_info = {
                "email": payload.get("sub"),
                "user_id": payload.get("userId"),
                "roles": payload.get("roles", []),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "iss": payload.get("iss")
            }

            return user_info
        except Exception as e:
            print_error(f"Failed to extract user from token: {e}")
            return None

    def is_token_expired(self, token: str) -> bool:
        """Check if JWT token is expired"""
        try:
            import jwt
            decoded = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False, "verify_exp": True})
            return False  # Token is not expired
        except jwt.ExpiredSignatureError:
            return True  # Token is expired
        except Exception:
            return True  # Assume expired if can't decode

    def calculate_session_duration(self, token: str) -> Optional[int]:
        """Calculate session duration in seconds from JWT token"""
        try:
            user_info = self.extract_user_from_token(token)
            if not user_info or not user_info.get("iat") or not user_info.get("exp"):
                return None

            iat = user_info["iat"]
            exp = user_info["exp"]
            return exp - iat
        except Exception:
            return None

    def get_user_from_database(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user information from database"""
        try:
            query = """
                SELECT id, email, email_verified_at, created_at, updated_at
                FROM users
                WHERE email = %s
            """
            results = self.db_helper.execute_query(query, (email,))
            return results[0] if results else None
        except Exception as e:
            print_error(f"Failed to get user from database: {e}")
            return None

    def print_auth_summary(self, email: str, token: str = None):
        """Print authentication summary for debugging"""
        print_info(f"Authentication Summary for: {email}")

        user = self.get_user_from_database(email)
        if user:
            print_info(f"  User ID: {user.get('id')}")
            print_info(f"  Email Verified: {'Yes' if user.get('email_verified_at') else 'No'}")
            print_info(f"  Created: {user.get('created_at')}")

        if token:
            validation = self.validate_jwt_token(token)
            print_info(f"  Token Valid: {'Yes' if validation['is_valid'] else 'No'}")
            if validation['is_valid']:
                user_info = self.extract_user_from_token(token)
                if user_info:
                    print_info(f"  Token Email: {user_info.get('email')}")
                    print_info(f"  Token User ID: {user_info.get('user_id')}")
                    print_info(f"  Token Roles: {', '.join(user_info.get('roles', []))}")

                    duration = self.calculate_session_duration(token)
                    if duration:
                        hours = duration // 3600
                        minutes = (duration % 3600) // 60
                        print_info(f"  Session Duration: {hours}h {minutes}m")

    def admin_login(self) -> TestStep:
        """
        Admin login for test setup
        Returns TestStep with JWT token for admin operations
        """
        from uat_framework import TestStep, extract_jwt_token
        from uat_config import config

        step = TestStep(
            step_number=1,
            step_name="Admin Login",
            status="PASS",
            message="Login as admin user"
        )

        try:
            admin_login_data = {
                "email": config.admin_email,
                "password": config.admin_password
            }

            response, response_time = self.http_client.post("/api/customers/login", admin_login_data)

            if response.status_code == 200:
                jwt_token = extract_jwt_token(response)

                step.result = {
                    "jwt_token": jwt_token,
                    "response_time": response_time
                }
                step.status = "PASS"
                print_success("Admin login successful")
                return step
            else:
                step.status = "FAIL"
                step.message = f"Admin login failed: {response.status_code}"
                return step

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin login exception: {e}"
            return step

    def create_invite_codes(self, admin_token: str, count: int = 1) -> TestStep:
        """
        Create invite codes using admin token
        Returns TestStep with created invite codes
        """
        from uat_framework import TestStep
        from uat_config import config

        step = TestStep(
            step_number=2,
            step_name="Create Invite Codes",
            status="PASS",
            message=f"Create {count} invite code(s)"
        )

        try:
            # Generate unique invite code
            from uat_config import config
            test_code = config.generate_unique_invite_code("IMG-SOLVE-TEST")
            invite_code_data = {"code": test_code}

            response, response_time = self.http_client.post(
                config.get_endpoint('admin_invites'),
                invite_code_data,
                auth_token=admin_token
            )

            if response.status_code == 200:
                step.result = {
                    "codes": [test_code],  # Return as list to match expected usage
                    "response_time": response_time
                }
                step.status = "PASS"
                print_success(f"Created invite code: {test_code}")
                return step
            else:
                step.status = "FAIL"
                step.message = f"Invite code creation failed: {response.status_code}"
                return step

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Invite code creation exception: {e}"
            return step

    def register_user(
        self,
        email: str,
        password: str,
        invite_code: str
    ) -> TestStep:
        """
        Register a user with an invite code
        Returns TestStep with user registration result
        """
        from uat_framework import TestStep

        step = TestStep(
            step_number=3,
            step_name="Register User",
            status="PASS",
            message="Register new user with invite code"
        )

        try:
            user_data = {
                "email": email,
                "password": password,
                "confirmPassword": password,
                "inviteCode": invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            response, response_time = self.http_client.post("/api/customers/register", user_data)

            if response.status_code in [201, 202]:
                step.result = {
                    "email": email,
                    "response_time": response_time,
                    "status_code": response.status_code
                }
                step.status = "PASS"
                print_success(f"User registered: {email}")
                return step
            else:
                step.status = "FAIL"
                step.message = f"User registration failed: {response.status_code}"
                return step

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User registration exception: {e}"
            return step

    def customer_login(self, email: str, password: str) -> TestStep:
        """
        Login as a customer/user
        Returns TestStep with JWT token and user info
        """
        from uat_framework import TestStep, extract_jwt_token

        step = TestStep(
            step_number=4,
            step_name="Customer Login",
            status="PASS",
            message="Login as customer/user"
        )

        try:
            login_data = {
                "email": email,
                "password": password
            }

            response, response_time = self.http_client.post("/api/customers/login", login_data)

            if response.status_code == 200:
                jwt_token = extract_jwt_token(response)

                # Get user info from the response for the customer login
                login_result = response.json()

                step.result = {
                    "email": email,
                    "jwt_token": jwt_token,
                    "user_id": login_result.get('id'),  # This may need adjustment based on actual API response
                    "response_time": response_time
                }
                step.status = "PASS"
                print_success(f"User login successful: {email}")
                return step
            else:
                step.status = "FAIL"
                step.message = f"User login failed: {response.status_code}"
                return step

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User login exception: {e}"
            return step


class AuthDataManager:
    """Data management for authentication tests"""

    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper

    def cleanup_test_user(self, email: str) -> bool:
        """Clean up test user and related data"""
        try:
            user_id = self.db_helper.get_user_id(email)
            if not user_id:
                return True  # User doesn't exist, nothing to cleanup

            # Clean up API tokens
            self.db_helper.execute_update("DELETE FROM api_tokens WHERE user_id = %s", (user_id,))

            # Clean up request logs
            self.db_helper.execute_update("DELETE FROM request_logs WHERE user_id = %s", (user_id,))

            # Clean up billing periods
            self.db_helper.execute_update("DELETE FROM billing_periods WHERE user_id = %s", (user_id,))

            # Delete user
            self.db_helper.execute_update("DELETE FROM users WHERE id = %s", (user_id,))

            return True
        except Exception as e:
            print_error(f"Failed to cleanup test user {email}: {e}")
            return False

    def cleanup_test_invite_code(self, code: str) -> bool:
        """Clean up test invite code"""
        try:
            self.db_helper.execute_update("DELETE FROM invite_codes WHERE code = %s", (code,))
            return True
        except Exception as e:
            print_error(f"Failed to cleanup invite code {code}: {e}")
            return False

    def get_test_user_count(self) -> int:
        """Get count of test users (emails with test- pattern)"""
        try:
            query = "SELECT COUNT(*) as count FROM users WHERE email LIKE '%test%'"
            results = self.db_helper.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception:
            return 0

    def get_active_invite_code_count(self) -> int:
        """Get count of active invite codes"""
        try:
            query = "SELECT COUNT(*) as count FROM invite_codes WHERE is_active = true"
            results = self.db_helper.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception:
            return 0
