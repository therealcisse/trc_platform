#!/usr/bin/env python3
"""
UAT Test Framework for Billing API Testing
Self-contained framework with all utilities needed for billing tests
"""

import sys
import os
import json
import time
import jwt
import requests
import psycopg2
import psycopg2.extras
import colorama
import bcrypt
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

# Initialize colorama for colored output
colorama.init(autoreset=True)

# ANSI color codes
class Colors:
    GREEN = colorama.Fore.GREEN
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    BLUE = colorama.Fore.BLUE
    MAGENTA = colorama.Fore.MAGENTA
    CYAN = colorama.Fore.CYAN
    WHITE = colorama.Fore.WHITE
    RESET = colorama.Style.RESET_ALL

@dataclass
class TestStep:
    """Individual test step result"""
    step_number: int
    step_name: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    message: str
    response_time: Optional[float] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None
    database_state: Optional[Dict[str, Any]] = None
    screenshots: List[str] = field(default_factory=list)

    def is_success(self) -> bool:
        return self.status in ['PASS', 'SKIP']

@dataclass
class TestResult:
    """Complete test result"""
    test_id: str
    test_name: str
    status: str  # 'PASS', 'FAIL', 'SKIP', 'ERROR'
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    error_steps: int
    total_time: float
    start_time: datetime
    end_time: Optional[datetime] = None
    test_steps: List[TestStep] = field(default_factory=list)
    evidence_files: List[str] = field(default_factory=list)
    environment_info: Dict[str, str] = field(default_factory=dict)

    def is_success(self) -> bool:
        return self.status == 'PASS'

    def get_success_rate(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return (self.passed_steps / self.total_steps) * 100

class DatabaseHelper:
    """Database connection and operations utility"""

    def __init__(self, database_url: str = "postgresql://localhost:5432/trc_platform"):
        self.database_url = database_url
        self.connection = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                self.database_url,
                connect_timeout=10,
                cursor_factory=psycopg2.extras.RealDictCursor
            )

            # Test connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

            print(f"{Colors.GREEN}✓ Database connection established{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}❌ Database connection failed: {e}{Colors.RESET}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SQL query and return results"""
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            results = []
            for row in rows:
                if hasattr(row, 'items'):  # RealDictRow object
                    results.append(dict(row))
                else:  # Regular tuple
                    results.append(dict(zip(columns, row)))

            return results
        except Exception as e:
            print(f"{Colors.RED}❌ Database query failed: {e}{Colors.RESET}")
            return []

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute an INSERT, UPDATE, or DELETE query and return success status"""
        if not self.connection:
            raise Exception("No database connection")

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()

            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
        except Exception as e:
            print_error(f"Update query execution failed: {e}")
            if self.connection:
                self.connection.rollback()
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()

    def execute_update_with_count(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return affected row count"""
        if not self.connection:
            raise Exception("No database connection")
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Exception as e:
            print_error(f"Update query execution failed: {e}")
            if self.connection:
                self.connection.rollback()
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()

    def verify_user_email_directly(self, email: str) -> bool:
        """Directly verify user email for testing purposes"""
        try:
            query = "UPDATE users SET email_verified_at = NOW() WHERE email = %s RETURNING id"
            results = self.execute_query(query, (email,))
            return len(results) > 0
        except Exception as e:
            print(f"{Colors.RED}Failed to verify user email: {e}{Colors.RESET}")
            return False

class EmailVerificationHelper:
    """Email verification via Mailcatcher"""

    def __init__(self, mailcatcher_url: str = "http://localhost:1080"):
        self.mailcatcher_url = mailcatcher_url
        self.session = requests.Session()

    def connect_mailcatcher(self) -> bool:
        """Connect to Mailcatcher API"""
        try:
            response = self.session.get(f"{self.mailcatcher_url}/messages")
            if response.status_code == 200:
                print(f"{Colors.GREEN}✓ Mailcatcher connected successfully{Colors.RESET}")
                return True
            else:
                print(f"{Colors.RED}❌ Mailcatcher unavailable: {response.status_code}{Colors.RESET}")
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ Mailcatcher connection failed: {e}{Colors.RESET}")
            return False

    def get_latest_email(self, recipient_email: str) -> Optional[Dict]:
        """Get latest email for specific recipient"""
        try:
            response = self.session.get(f"{self.mailcatcher_url}/messages")
            if response.status_code == 200:
                messages = response.json()
                for message in messages:
                    recipients = message.get('recipients', [])
                    clean_recipients = [r.strip('<>') for r in recipients]
                    if recipient_email in clean_recipients:
                        return message
                return None
            else:
                print(f"{Colors.YELLOW}⚠ No emails found for {recipient_email}{Colors.RESET}")
                return None
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to fetch emails: {e}{Colors.RESET}")
            return None

    def extract_verification_token(self, email: Dict) -> Optional[str]:
        """Extract verification token from email body or links"""
        try:
            message_id = email.get('id')
            if not message_id:
                return None

            response = self.session.get(f"{self.mailcatcher_url}/messages/{message_id}.html")
            if response.status_code != 200:
                return None

            body = response.text
            body_lower = body.lower()

            if '/verify-email?token=' in body_lower:
                start_index = body_lower.find('/verify-email?token=')
                if start_index != -1:
                    start_index += len('/verify-email?token=')
                    token = body[start_index:]
                    end_index = token.find('"')
                    if end_index != -1:
                        token = token[:end_index]
                    return token

            if 'token=' in body_lower:
                start_index = body_lower.find('token=')
                if start_index != -1:
                    start_index += len('token=')
                    end_index = body.find('"', start_index)
                    if end_index != -1:
                        token = body[start_index:end_index]
                    return token

            return None
        except Exception as e:
            print(f"{Colors.YELLOW}⚠ Could not extract verification token: {e}{Colors.RESET}")
            return None

    def clear_all_emails(self):
        """Clear all emails in Mailcatcher"""
        try:
            response = self.session.delete(f"{self.mailcatcher_url}/messages")
            if response.status_code == 200:
                print(f"{Colors.GREEN}✅ All emails cleared from Mailcatcher{Colors.RESET}")
                return True
            else:
                print(f"{Colors.YELLOW}⚠ Could not clear emails: {response.status_code}{Colors.RESET}")
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ Failed to clear emails: {e}{Colors.RESET}")
            return False

class HTTPClient:
    """HTTP client with authentication support"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def post(self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str] = None, auth_token: str = None, api_token: str = None) -> Tuple[requests.Response, float]:
        """Make POST request"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers}

        if headers:
            request_headers.update(headers)

        if auth_token:
            request_headers['Authorization'] = f"Bearer {auth_token}"
        elif api_token:
            request_headers['X-API-Token'] = api_token

        try:
            start_time = time.time()
            response = self.session.post(url, json=data, headers=request_headers, timeout=60)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP request failed: {e}{Colors.RESET}")
            raise e

    def get(self, endpoint: str, headers: Dict[str, str] = None, auth_token: str = None, api_token: str = None) -> Tuple[requests.Response, float]:
        """Make GET request"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers}

        if headers:
            request_headers.update(headers)

        if auth_token:
            request_headers['Authorization'] = f"Bearer {auth_token}"
        elif api_token:
            request_headers['X-API-Token'] = api_token

        try:
            start_time = time.time()
            response = self.session.get(url, headers=request_headers, timeout=60)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP GET request failed: {e}{Colors.RESET}")
            raise e

    def put(self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str] = None, auth_token: str = None, api_token: str = None) -> Tuple[requests.Response, float]:
        """Make PUT request"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers}

        if headers:
            request_headers.update(headers)

        if auth_token:
            request_headers['Authorization'] = f"Bearer {auth_token}"
        elif api_token:
            request_headers['X-API-Token'] = api_token

        try:
            start_time = time.time()
            response = self.session.put(url, json=data, headers=request_headers, timeout=60)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP PUT request failed: {e}{Colors.RESET}")
            raise e

    def delete(self, endpoint: str, headers: Dict[str, str] = None, auth_token: str = None, api_token: str = None) -> Tuple[requests.Response, float]:
        """Make DELETE request"""
        url = f"{self.base_url}{endpoint}"
        request_headers = {**self.default_headers}

        if headers:
            request_headers.update(headers)

        if auth_token:
            request_headers['Authorization'] = f"Bearer {auth_token}"
        elif api_token:
            request_headers['X-API-Token'] = api_token

        try:
            start_time = time.time()
            response = self.session.delete(url, headers=request_headers, timeout=60)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP DELETE request failed: {e}{Colors.RESET}")
            raise e

class TokenManager:
    """JWT and API token management utility"""

    def __init__(self):
        self.tokens = {}

    def store_token(self, name: str, token: str):
        """Store token for later use"""
        self.tokens[name] = token
        print(f"{Colors.BLUE}💾 Stored {name} token for later use{Colors.RESET}")

    def get_token(self, name: str) -> Optional[str]:
        """Retrieve stored token"""
        return self.tokens.get(name)

    def validate_jwt_format(self, token: str) -> bool:
        """Basic JWT format validation"""
        try:
            parts = token.split('.')
            return len(parts) == 3 and all(part.strip() for part in parts)
        except:
            return False

class TestReporting:
    """Test result reporting and formatting"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.end_time = None

    def add_test_result(self, result: TestResult):
        """Add test result to tracking"""
        self.test_results.append(result)

    def set_end_time(self):
        """Mark test completion time"""
        self.end_time = datetime.now()

    def print_test_header(self, test_id: str, test_name: str):
        """Print test header"""
        print(f"\n{'='*80}")
        print(f"{'='*80}")
        print(f"🧪 STARTING {test_id}: {test_name}")
        print(f"{'='*80}")
        print(f"{'='*80}\n")

    def print_test_footer(self, test_id: str, test_name: str, result: TestResult):
        """Print test footer"""
        status_color = Colors.GREEN if result.is_success() else Colors.RED
        print(f"\n{'='*80}")
        print(f"{'='*80}")
        print(f"{status_color}⏹ {test_id}: {test_name} - {result.status}{Colors.RESET}")
        print(f"{'='*80}")
        print(f"{'='*80}\n")

    def print_step_result(self, step: TestStep):
        """Print individual step result"""
        status_color = Colors.GREEN if step.is_success() else Colors.RED
        time_info = f" ({step.response_time:.0f}ms)" if step.response_time else ""

        print(f"  {step.step_number}. {step.step_name} - {status_color}{step.status}{Colors.RESET}{time_info}")
        if step.message:
            print(f"     {step.message}")

# Global utility functions
def extract_jwt_token(response: requests.Response) -> str:
    """Extract JWT token from response body"""
    try:
        data = response.json()
        return data.get('token', '')
    except:
        return ''

def extract_json_field(response: requests.Response, field: str) -> Any:
    """Extract field from JSON response"""
    try:
        data = response.json()
        return data.get(field)
    except:
        return None

def wait_for_email_verification(email_helper, email: str, timeout: int = 30) -> bool:
    """Wait for email to arrive in Mailcatcher"""
    start_time = time.time()
    email_found = False

    while time.time() - start_time < timeout:
        email_data = email_helper.get_latest_email(email)
        if email_data and email_helper.extract_verification_token(email_data):
            email_found = True
            break
        time.sleep(1)

    return email_found

def format_timestamp(timestamp: Optional[datetime]) -> str:
    """Format timestamp for display"""
    if not timestamp:
        return "NULL"
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def format_response_time(response_time: Optional[float]) -> str:
    """Format response time for display"""
    if response_time is None:
        return "N/A"
    return f"{response_time:.0f}ms"

def print_section_header(title: str):
    """Print formatted section header"""
    print(f"\n# {title}")
    print(f"{'='*(len(title)+4)}")
    print(f"{'='*(len(title)+4)}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")