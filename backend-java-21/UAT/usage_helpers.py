#!/usr/bin/env python3
"""
Usage Helpers for TRC Platform UAT Testing
Provides utilities for testing /api/usage/requests endpoint
including data generation, validation, and test scenario management
"""

import sys
import os
import json
import uuid
import time
import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timedelta

# Import UAT framework
from uat_framework import (
    DatabaseHelper,
    HTTPClient,
    TokenManager,
    TestReporting,
    TestStep,
    TestResult,
    Colors,
    print_success,
    print_error,
    print_warning,
    print_info,
    extract_jwt_token,
    wait_for_email_verification,
    EmailVerificationHelper,
)

@dataclass
class UsageRequestData:
    """Test data structure for usage request logs"""
    id: str
    user_id: str
    request_ts: str
    service: str
    status: str
    duration_ms: int
    request_bytes: int
    response_bytes: int
    request_id: str
    flow_id: Optional[str] = None
    token_prefix: Optional[str] = None
    billing_period_id: Optional[str] = None
    token_id: Optional[str] = None

class UsageHelper:
    """Helper class for usage-related testing operations"""

    def __init__(self, db_helper: DatabaseHelper = None, http_client: HTTPClient = None):
        self.db_helper = db_helper or DatabaseHelper("postgresql://trc_user:trc_password@localhost:5432/trc_platform")
        self.http_client = http_client or HTTPClient()
        self.test_data_prefix = f"uat_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def create_usage_test_user(self, email: str = None, password: str = None) -> Dict[str, Any]:
        """Create a dedicated test user for usage testing"""
        if not email:
            email = f"{self.test_data_prefix}@uat-test.trc-platform.local"

        if not password:
            password = "UsageTest123!@#"

        print_info(f"Creating usage test user: {email}")

        # First, get admin token to create invite codes
        admin_login_data = {
            "email": "admin@trc-platform.local",
            "password": "password"
        }

        admin_response, _ = self.http_client.post("/api/customers/login", data=admin_login_data)
        if admin_response.status_code != 200:
            raise Exception("Failed to login as admin to create invite codes")

        admin_token = admin_response.json()['token']

        # Create a single invite code
        import uuid
        invite_code = f"USAGE-{uuid.uuid4().hex[:8].upper()}"

        # Set expiration to 7 days from now
        from datetime import datetime, timedelta
        expires_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

        invite_data = {
            "code": invite_code,
            "expiresAt": expires_at
        }

        invite_response, _ = self.http_client.post("/api/v1/admin/invites", data=invite_data, auth_token=admin_token)
        if invite_response.status_code not in [200, 201]:
            raise Exception(f"Failed to create invite code: {invite_response.status_code} - {invite_response.text}")

        invite_result = invite_response.json()
        if not invite_result or 'code' not in invite_result:
            raise Exception("Invalid invite code response")

        invite_code = invite_result['code']

        # Register user
        register_data = {
            "email": email,
            "password": password,
            "confirmPassword": password,
            "inviteCode": invite_code,
            "userAcceptedTerms": True,
            "userAcknowledgedDisclaimer": True
        }

        response, response_time = self.http_client.post("/api/customers/register", data=register_data)

        if response.status_code not in [201, 202]:
            raise Exception(f"Failed to create usage test user: {response.status_code} - {response.text}")

        user_data = response.json() if response.status_code == 201 else {"email": email, "id": "temp-id"}

        # Wait for email verification
        email_helper = EmailVerificationHelper("http://localhost:1080")
        if not wait_for_email_verification(email_helper, email):
            raise Exception("Failed to verify email for usage test user")

        # Login to get JWT token
        login_data = {
            "email": email,
            "password": password
        }

        db_helper = DatabaseHelper()
        db_helper.verify_user_email_directly(email)

        response, response_time = self.http_client.post("/api/customers/login", data=login_data)

        if response.status_code != 200:
            raise Exception(f"Failed to login usage test user: {response.status_code} - {response.text}")

        login_result = response.json()
        jwt_token = extract_jwt_token(login_result)

        return {
            "user": user_data,
            "jwt_token": jwt_token,
            "email": email,
            "password": password
        }


    def generate_sample_request_logs(self, user_id: str, count: int = 20) -> List[UsageRequestData]:
        """Generate sample request log data for testing"""
        request_logs = []

        # Use a consistent reference time - midnight of yesterday (to avoid today's data in date filtering tests)
        base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

        services = ["core.image_solve", "core.text_solve", "core.analysis", "core.processing"]
        statuses = ["SUCCESS", "ERROR"]

        for i in range(count):
            # Generate timestamps spread over the last 30 days
            # Each log is 1 day apart, distributed from today (day 0) back to 29 days ago
            days_ago = i

            request_ts = base_time - timedelta(days=days_ago)

            # Random service and status (mostly success)
            service = services[i % len(services)]
            status = "SUCCESS" if i % 10 != 0 else "ERROR"  # 10% error rate

            # Generate realistic metrics
            duration_ms = 500 + (i * 100) + (hash(str(i)) % 2000)  # 500-3500ms
            request_bytes = 1024 + (hash(str(i)) % 5120)  # 1KB-6KB
            response_bytes = 2048 + (hash(str(i * 2)) % 10240)  # 2KB-12KB

            request_log = UsageRequestData(
                id=str(uuid.uuid4()),
                user_id=user_id,
                request_ts=request_ts.isoformat(),
                service=service,
                status=status,
                duration_ms=duration_ms,
                request_bytes=request_bytes,
                response_bytes=response_bytes,
                request_id=str(uuid.uuid4()),
                flow_id=f"flow_{i}" if i % 3 == 0 else None,
                token_prefix=f"trc_{hash(str(i)) % 10000:04d}" if i % 2 == 0 else None
            )

            request_logs.append(request_log)

        return request_logs

    def insert_request_logs_to_database(self, request_logs: List[UsageRequestData]) -> bool:
        """Insert generated request logs into the database"""
        try:
            if not self.db_helper.connect():
                raise Exception("Failed to connect to database")
            conn = self.db_helper.connection
            cursor = conn.cursor()

            for log in request_logs:
                # Convert timestamp to datetime object for database
                request_ts = datetime.fromisoformat(log.request_ts.replace('Z', '+00:00'))

                # Simplified: Don't try to find billing periods for testing
                billing_period_id = None
                token_id = None

                # Find API token if token_prefix is provided
                if log.token_prefix:
                    cursor.execute("""
                        SELECT id FROM api_tokens
                        WHERE user_id = %s
                        AND token_prefix = %s
                    """, (log.user_id, log.token_prefix))
                    token_result = cursor.fetchone()
                    if token_result:
                        token_id = token_result[0]

                # Insert request log
                cursor.execute("""
                    INSERT INTO request_logs (
                        id, user_id, token_id, billing_period_id,
                        service, request_ts, duration_ms,
                        request_bytes, response_bytes, status,
                        request_id, flow_id, result
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    log.id, log.user_id, token_id, billing_period_id,
                    log.service, request_ts, log.duration_ms,
                    log.request_bytes, log.response_bytes, log.status,
                    log.request_id, log.flow_id, None  # result is null for test data
                ))

            conn.commit()
            cursor.close()
            # Don't close connection here - let the DatabaseHelper manage it
            # self.db_helper.disconnect()  # Uncomment if we want explicit cleanup

            print_success(f"Inserted {len(request_logs)} request logs to database")
            return True

        except Exception as e:
            print_error(f"Failed to insert request logs: {str(e)}")
            return False

    def get_usage_requests(self, token: str, from_date: str = None,
                          to_date: str = None, page: int = 0, size: int = 25) -> Dict[str, Any]:
        """Make authenticated request to usage endpoint"""

        # Set authentication header
        headers = {"Authorization": f"Bearer {token}"}

        # Build query parameters
        params = {"page": page, "size": size}
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        response = requests.get(
            f"{self.http_client.base_url}/api/usage/requests",
            headers=headers,
            params=params,
            timeout=30
        )

        return {
            "status_code": response.status_code,
            "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }

    def validate_usage_response_structure(self, response_data: Dict[str, Any]) -> List[str]:
        """Validate the response structure from usage endpoint"""
        errors = []

        # Check required top-level fields
        required_fields = ["content", "pageable", "last", "totalPages", "totalElements",
                          "size", "number", "sort", "first", "numberOfElements", "empty"]

        for field in required_fields:
            if field not in response_data:
                errors.append(f"Missing required field: {field}")

        # Check content structure if not empty
        if "content" in response_data and response_data["content"]:
            sample_item = response_data["content"][0]
            required_item_fields = ["id", "requestTs", "service", "status",
                                   "durationMs", "requestBytes", "responseBytes", "requestId"]

            for field in required_item_fields:
                if field not in sample_item:
                    errors.append(f"Missing required field in content item: {field}")

            # Check data types
            if "requestTs" in sample_item:
                try:
                    datetime.fromisoformat(sample_item["requestTs"].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    errors.append("requestTs is not a valid ISO datetime")

            if "durationMs" in sample_item and not isinstance(sample_item["durationMs"], int):
                errors.append("durationMs should be an integer")

            if "requestBytes" in sample_item and not isinstance(sample_item["requestBytes"], int):
                errors.append("requestBytes should be an integer")

            if "responseBytes" in sample_item and not isinstance(sample_item["responseBytes"], int):
                errors.append("responseBytes should be an integer")

        # Check pagination structure
        if "pageable" in response_data:
            pageable = response_data["pageable"]
            required_pageable_fields = ["sort", "offset", "pageNumber", "pageSize", "paged", "unpaged"]

            for field in required_pageable_fields:
                if field not in pageable:
                    errors.append(f"Missing required field in pageable: {field}")

        return errors

    def validate_date_filtering(self, response_data: Dict[str, Any],
                               from_date: str = None, to_date: str = None) -> List[str]:
        """Validate that date filtering is working correctly"""
        errors = []

        if not response_data.get("content"):
            return errors  # No content to validate

        try:
            # Parse filter dates
            from_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00')) if from_date else None
            # For to_date, interpret as end of day (23:59:59) to be more lenient
            if to_date:
                to_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
                to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                to_dt = None

            # Check each response item
            for item in response_data["content"]:
                item_ts = datetime.fromisoformat(item["requestTs"].replace('Z', '+00:00'))

                if from_dt and item_ts < from_dt:
                    errors.append(f"Item {item['id']} is before from_date filter")

                if to_dt and item_ts > to_dt:
                    errors.append(f"Item {item['id']} is after to_date filter")

        except ValueError as e:
            errors.append(f"Date parsing error: {str(e)}")

        return errors

    def validate_pagination(self, response_data: Dict[str, Any], expected_page: int, expected_size: int) -> List[str]:
        """Validate pagination parameters"""
        errors = []

        # Check page number
        if response_data.get("number") != expected_page:
            errors.append(f"Expected page {expected_page}, got {response_data.get('number')}")

        # Check page size
        if response_data.get("size") != expected_size:
            errors.append(f"Expected size {expected_size}, got {response_data.get('size')}")

        # Check pagination consistency
        total_elements = response_data.get("totalElements", 0)
        page_size = response_data.get("size", 0)
        current_page = response_data.get("number", 0)
        number_of_elements = response_data.get("numberOfElements", 0)

        # Verify total pages calculation
        expected_total_pages = (total_elements + page_size - 1) // page_size if page_size > 0 else 0
        if response_data.get("totalPages") != expected_total_pages:
            errors.append(f"Total pages calculation mismatch: expected {expected_total_pages}, got {response_data.get('totalPages')}")

        # Verify numberOfElements doesn't exceed size
        if number_of_elements > page_size:
            errors.append(f"numberOfElements ({number_of_elements}) exceeds page size ({page_size})")

        return errors

    def cleanup_usage_test_data(self, test_prefix: str = None) -> bool:
        """Clean up test data created during usage testing"""
        try:
            prefix = test_prefix or self.test_data_prefix

            if not self.db_helper.connect():
                raise Exception("Failed to connect to database")
            conn = self.db_helper.connection
            cursor = conn.cursor()

            # Delete request logs
            cursor.execute("""
                DELETE FROM request_logs
                WHERE user_id IN (
                    SELECT id FROM users
                    WHERE email LIKE %s
                )
            """, (f"{prefix}%",))

            deleted_logs = cursor.rowcount

            # Delete API tokens
            cursor.execute("""
                DELETE FROM api_tokens
                WHERE user_id IN (
                    SELECT id FROM users
                    WHERE email LIKE %s
                )
            """, (f"{prefix}%",))

            deleted_tokens = cursor.rowcount

            # Delete invite codes BEFORE users to avoid foreign key constraint violations
            cursor.execute("""
                DELETE FROM invite_codes
                WHERE code LIKE %s OR used_by_user_id IN (
                    SELECT id FROM users
                    WHERE email LIKE %s
                )
            """, (f"{prefix}%", f"{prefix}%"))

            deleted_invite_codes = cursor.rowcount

            # Delete users
            cursor.execute("""
                DELETE FROM users
                WHERE email LIKE %s
            """, (f"{prefix}%",))

            deleted_users = cursor.rowcount

            conn.commit()
            cursor.close()
            # Don't close connection here

            print_success(f"Cleaned up: {deleted_users} users, {deleted_tokens} tokens, {deleted_invite_codes} invite codes, {deleted_logs} request logs")
            return True

        except Exception as e:
            print_error(f"Failed to cleanup usage test data: {str(e)}")
            return False

class UsageDataManager:
    """Manages test data lifecycle for usage testing"""

    def __init__(self):
        self.helper = UsageHelper()
        self.created_users = []
        self.created_request_logs = []

    def create_test_user_with_data(self, email: str = None, log_count: int = 20) -> Dict[str, Any]:
        """Create a test user and populate with usage data"""
        user_data = self.helper.create_usage_test_user(email)

        # Generate and insert request logs
        request_logs = self.helper.generate_sample_request_logs(
            user_data["user"]["id"], log_count
        )

        if self.helper.insert_request_logs_to_database(request_logs):
            self.created_users.append(user_data)
            self.created_request_logs.extend(request_logs)

            return {
                **user_data,
                "jwt_token": user_data["jwt_token"],
                "request_logs_count": len(request_logs)
            }
        else:
            raise Exception("Failed to insert request logs")

    def cleanup_all(self):
        """Clean up all created test data"""
        prefix = self.helper.test_data_prefix
        self.helper.cleanup_usage_test_data(prefix)
        self.created_users.clear()
        self.created_request_logs.clear()

    def get_helper(self) -> UsageHelper:
        """Get the underlying UsageHelper instance"""
        return self.helper

# Date format utilities for testing
class DateTestUtils:
    """Utilities for testing various date formats"""

    @staticmethod
    def get_test_date_formats(base_date: datetime = None) -> Dict[str, str]:
        """Get various date format representations of the same date"""
        if not base_date:
            base_date = datetime.now()

        return {
            "iso_format": base_date.isoformat(),
            "date_only": base_date.strftime("%Y-%m-%d"),
            "date_time": base_date.strftime("%Y-%m-%d %H:%M:%S"),
            "iso_with_z": base_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "yesterday": (base_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            "tomorrow": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "last_week": (base_date - timedelta(days=7)).strftime("%Y-%m-%d"),
            "next_week": (base_date + timedelta(days=7)).strftime("%Y-%m-%d")
        }

    @staticmethod
    def get_invalid_date_formats() -> List[str]:
        """Get list of invalid date formats for negative testing"""
        return [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "2024/01/01",  # Wrong separator
            "01-01-2024",  # Wrong format
            "Jan 1, 2024", # Text month
            "",            # Empty string
            "not-a-date",  # Completely invalid
            "2024-01-01T25:00:00",  # Invalid hour
            "2024-01-01 24:00:00"   # Invalid hour
        ]
