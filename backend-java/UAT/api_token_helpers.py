#!/usr/bin/env python3
"""
API Token Helpers for TRC Platform UAT Testing
API token-specific validation and utility functions.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from uat_framework import DatabaseHelper, HTTPClient, Colors, print_info, print_error


class ApiTokenHelper:
    """API Token specific operations and validation"""

    def __init__(self, db_helper: DatabaseHelper, http_client: HTTPClient):
        self.db_helper = db_helper
        self.http_client = http_client

    def validate_token_format(self, token: str) -> bool:
        """Validate API token format"""
        if not token or not isinstance(token, str):
            return False

        # Check for tok_ prefix
        if not token.startswith('tok_'):
            return False

        # Check length (tok_ + base64url of 32 bytes = 43 chars)
        if len(token) != 47:  # 4 + 43
            return False

        # Check if the rest is valid base64url characters
        token_body = token[4:]  # Remove 'tok_' prefix
        base64url_pattern = re.compile(r'^[A-Za-z0-9_-]+$')
        return bool(base64url_pattern.match(token_body))

    def validate_token_hash(self, plain_token: str, stored_hash: str) -> bool:
        """Validate token against stored hash"""
        try:
            import bcrypt
            return bcrypt.checkpw(plain_token.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            return False

    def extract_token_prefix(self, token: str) -> str:
        """Extract token prefix (first 12 characters)"""
        if len(token) >= 12:
            return token[:12]
        return token

    def is_token_expired(self, expires_at: Optional[str]) -> bool:
        """Check if token is expired"""
        if not expires_at:
            return False

        try:
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            return current_time >= expiry_time
        except Exception:
            return True  # Assume expired if can't parse

    def create_token_data(self, name: str, expires_at: Optional[str] = None) -> Dict[str, Any]:
        """Create token creation request data"""
        data = {"name": name}
        if expires_at:
            data["expiresAt"] = expires_at
        return data

    def create_token_expiration_date(self, days_from_now: int = 30) -> str:
        """Create token expiration date string"""
        expiry = datetime.now(timezone.utc) + datetime.timedelta(days=days_from_now)
        return expiry.isoformat().replace('+00:00', 'Z')

    def validate_token_name(self, name: str) -> Dict[str, Any]:
        """Validate token name requirements"""
        result = {
            "is_valid": True,
            "errors": []
        }

        if not name or not isinstance(name, str):
            result["errors"].append("Token name must be a non-empty string")
            result["is_valid"] = False
            return result

        if len(name.strip()) == 0:
            result["errors"].append("Token name cannot be empty or whitespace")
            result["is_valid"] = False
            return result

        if len(name) > 255:
            result["errors"].append("Token name cannot exceed 255 characters")
            result["is_valid"] = False

        if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
            result["errors"].append("Token name can only contain letters, numbers, spaces, hyphens, and underscores")
            result["is_valid"] = False

        return result

    def verify_token_created(self, user_id: str, token_name: str) -> bool:
        """Verify token was created for user"""
        return self.db_helper.check_token_exists(user_id, token_name)

    def get_user_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tokens for a user"""
        return self.db_helper.get_user_tokens(user_id)

    def get_token_details(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed token information"""
        return self.db_helper.get_token_by_id(token_id)

    def verify_token_revoked(self, token_id: str) -> bool:
        """Verify token was revoked"""
        return self.db_helper.verify_token_revoked(token_id)

    def get_token_usage_count(self, token_id: str) -> int:
        """Get token usage count"""
        return self.db_helper.get_token_usage_count(token_id)

    def verify_token_usage_updated(self, token_id: str) -> bool:
        """Verify token usage timestamp was updated"""
        return self.db_helper.verify_token_usage_update(token_id)

    def extract_token_from_response(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract token from API response"""
        # Common response field names for tokens
        possible_fields = ['token', 'apiToken', 'apiKey', 'accessToken']

        for field in possible_fields:
            if field in response_data:
                return response_data[field]

        # Check nested structures
        if 'data' in response_data and isinstance(response_data['data'], dict):
            for field in possible_fields:
                if field in response_data['data']:
                    return response_data['data'][field]

        return None

    def validate_token_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate token creation response structure"""
        result = {
            "is_valid": False,
            "errors": [],
            "token_fields": {}
        }

        if not isinstance(response_data, dict):
            result["errors"].append("Response data must be a dictionary")
            return result

        # Check for expected fields
        expected_fields = ['id', 'name', 'token', 'tokenPrefix', 'createdAt']
        for field in expected_fields:
            if field in response_data:
                result["token_fields"][field] = response_data[field]
            else:
                result["errors"].append(f"Missing required field: {field}")

        # Validate token format if present
        if 'token' in response_data:
            token = response_data['token']
            if not self.validate_token_format(token):
                result["errors"].append("Invalid token format in response")

        # Validate token prefix if present
        if 'tokenPrefix' in response_data and 'token' in response_data:
            token = response_data['token']
            expected_prefix = token[:12]
            actual_prefix = response_data['tokenPrefix']
            if actual_prefix != expected_prefix:
                result["errors"].append(f"Token prefix mismatch: expected {expected_prefix}, got {actual_prefix}")

        result["is_valid"] = len(result["errors"]) == 0
        return result

    def get_active_tokens_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active (non-revoked) tokens for user"""
        try:
            query = """
                SELECT id, name, token_prefix, created_at, last_used_at, expires_at
                FROM api_tokens
                WHERE user_id = %s AND revoked_at IS NULL
                ORDER BY created_at DESC
            """
            return self.db_helper.execute_query(query, (user_id,))
        except Exception as e:
            print_error(f"Failed to get active tokens: {e}")
            return []

    def get_revoked_tokens_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get revoked tokens for user"""
        try:
            query = """
                SELECT id, name, token_prefix, created_at, revoked_at
                FROM api_tokens
                WHERE user_id = %s AND revoked_at IS NOT NULL
                ORDER BY revoked_at DESC
            """
            return self.db_helper.execute_query(query, (user_id,))
        except Exception as e:
            print_error(f"Failed to get revoked tokens: {e}")
            return []

    def get_expired_tokens_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get expired tokens for user"""
        try:
            query = """
                SELECT id, name, token_prefix, created_at, expires_at
                FROM api_tokens
                WHERE user_id = %s AND expires_at IS NOT NULL AND expires_at < NOW()
                ORDER BY expires_at DESC
            """
            return self.db_helper.execute_query(query, (user_id,))
        except Exception as e:
            print_error(f"Failed to get expired tokens: {e}")
            return []

    def check_token_uniqueness(self, user_id: str, token_name: str) -> bool:
        """Check if token name is unique for user"""
        try:
            query = """
                SELECT COUNT(*) as count
                FROM api_tokens
                WHERE user_id = %s AND name = %s AND revoked_at IS NULL
            """
            results = self.db_helper.execute_query(query, (user_id, token_name))
            return results[0]['count'] == 0 if results else True
        except Exception:
            return False

    def calculate_token_age(self, created_at: str) -> Dict[str, int]:
        """Calculate token age in different units"""
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age = now - created

            return {
                "days": age.days,
                "hours": age.seconds // 3600,
                "minutes": (age.seconds % 3600) // 60,
                "total_hours": age.seconds // 3600 + (age.days * 24),
                "total_minutes": age.seconds // 60 + (age.days * 24 * 60)
            }
        except Exception:
            return {"days": 0, "hours": 0, "minutes": 0, "total_hours": 0, "total_minutes": 0}

    def format_token_info(self, token_info: Dict[str, Any]) -> str:
        """Format token information for display"""
        if not token_info:
            return "No token information available"

        lines = []
        lines.append(f"Token ID: {token_info.get('id', 'N/A')}")
        lines.append(f"Name: {token_info.get('name', 'N/A')}")
        lines.append(f"Prefix: {token_info.get('token_prefix', 'N/A')}")

        if 'created_at' in token_info:
            age = self.calculate_token_age(token_info['created_at'])
            lines.append(f"Created: {token_info['created_at']} ({age['days']} days ago)")

        if 'expires_at' in token_info and token_info['expires_at']:
            expired = self.is_token_expired(token_info['expires_at'])
            status = "EXPIRED" if expired else "ACTIVE"
            lines.append(f"Expires: {token_info['expires_at']} ({status})")

        if 'revoked_at' in token_info and token_info['revoked_at']:
            lines.append(f"Revoked: {token_info['revoked_at']}")

        if 'last_used_at' in token_info and token_info['last_used_at']:
            last_used_age = self.calculate_token_age(token_info['last_used_at'])
            lines.append(f"Last Used: {token_info['last_used_at']} ({last_used_age['days']} days ago)")

        usage_count = self.get_token_usage_count(token_info.get('id', ''))
        lines.append(f"Usage Count: {usage_count}")

        return "\n  ".join(lines)

    def print_token_summary(self, user_id: str):
        """Print comprehensive token summary for user"""
        print_info(f"Token Summary for User ID: {user_id}")

        active_tokens = self.get_active_tokens_for_user(user_id)
        revoked_tokens = self.get_revoked_tokens_for_user(user_id)
        expired_tokens = self.get_expired_tokens_for_user(user_id)

        print_info(f"  Active Tokens: {len(active_tokens)}")
        for token in active_tokens:
            print_info(f"    - {token['name']} ({token['token_prefix']})")
            print_info(f"      {self.format_token_info(token)}")

        if revoked_tokens:
            print_info(f"  Revoked Tokens: {len(revoked_tokens)}")
            for token in revoked_tokens:
                print_info(f"    - {token['name']} ({token['token_prefix']})")

        if expired_tokens:
            print_info(f"  Expired Tokens: {len(expired_tokens)}")
            for token in expired_tokens:
                print_info(f"    - {token['name']} ({token['token_prefix']})")


class ApiTokenDataManager:
    """Data management for API token tests"""

    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper

    def cleanup_user_tokens(self, user_id: str) -> bool:
        """Clean up all tokens for a user"""
        try:
            self.db_helper.execute_update("DELETE FROM api_tokens WHERE user_id = %s", (user_id,))
            return True
        except Exception as e:
            print_error(f"Failed to cleanup tokens for user {user_id}: {e}")
            return False

    def cleanup_token(self, token_id: str) -> bool:
        """Clean up specific token"""
        try:
            self.db_helper.execute_update("DELETE FROM api_tokens WHERE id = %s", (token_id,))
            return True
        except Exception as e:
            print_error(f"Failed to cleanup token {token_id}: {e}")
            return False

    def get_total_token_count(self) -> int:
        """Get total count of all tokens"""
        try:
            query = "SELECT COUNT(*) as count FROM api_tokens"
            results = self.db_helper.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception:
            return 0

    def get_active_token_count(self) -> int:
        """Get count of active tokens"""
        try:
            query = "SELECT COUNT(*) as count FROM api_tokens WHERE revoked_at IS NULL"
            results = self.db_helper.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception:
            return 0

    def get_revoked_token_count(self) -> int:
        """Get count of revoked tokens"""
        try:
            query = "SELECT COUNT(*) as count FROM api_tokens WHERE revoked_at IS NOT NULL"
            results = self.db_helper.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception:
            return 0

    def get_token_usage_stats(self) -> Dict[str, int]:
        """Get token usage statistics"""
        try:
            # Tokens with no usage
            no_usage_query = """
                SELECT COUNT(*) as count
                FROM api_tokens t
                LEFT JOIN request_logs r ON t.id = r.token_id
                WHERE r.token_id IS NULL
            """
            no_usage_results = self.db_helper.execute_query(no_usage_query)
            no_usage_count = no_usage_results[0]['count'] if no_usage_results else 0

            # Tokens with usage
            with_usage_query = """
                SELECT COUNT(DISTINCT t.id) as count
                FROM api_tokens t
                INNER JOIN request_logs r ON t.id = r.token_id
            """
            with_usage_results = self.db_helper.execute_query(with_usage_query)
            with_usage_count = with_usage_results[0]['count'] if with_usage_results else 0

            return {
                "total_tokens": self.get_total_token_count(),
                "active_tokens": self.get_active_token_count(),
                "revoked_tokens": self.get_revoked_token_count(),
                "tokens_with_usage": with_usage_count,
                "tokens_without_usage": no_usage_count
            }
        except Exception as e:
            print_error(f"Failed to get token usage stats: {e}")
            return {}

    def print_token_stats(self):
        """Print token statistics"""
        stats = self.get_token_usage_stats()

        print_info("Token Statistics:")
        print_info(f"  Total Tokens: {stats.get('total_tokens', 0)}")
        print_info(f"  Active Tokens: {stats.get('active_tokens', 0)}")
        print_info(f"  Revoked Tokens: {stats.get('revoked_tokens', 0)}")
        print_info(f"  Tokens With Usage: {stats.get('tokens_with_usage', 0)}")
        print_info(f"  Tokens Without Usage: {stats.get('tokens_without_usage', 0)}")