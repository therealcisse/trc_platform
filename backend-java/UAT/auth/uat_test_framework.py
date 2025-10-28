#!/usr/bin/env python3
"""
UAT Test Framework
Base framework for User Acceptance Testing of TRC Platform authentication system.
Provides common utilities, database connections, HTTP clients, and result tracking.
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
from pathlib import Path
import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

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
    start_time: datetime.datetime
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

@dataclass
class EnvironmentInfo:
    """Environment configuration and status"""
    app_url: str
    database_url: str
    mailcatcher_url: str
    app_status: str
    database_status: str
    mailcatcher_status: str
    java_version: Optional[str] = None
    spring_profile: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)

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
            print_info(f"DEBUG: Columns from cursor.description: {columns}")
            print_info(f"DEBUG: Rows from cursor.fetchall(): {rows}")
            print_info(f"DEBUG: Number of columns: {len(columns)}, Number of rows: {len(rows)}")

            results = []
            for row in rows:
                # Handle both regular tuples and RealDictRow objects
                if hasattr(row, 'items'):  # RealDictRow object
                    results.append(dict(row))
                else:  # Regular tuple
                    results.append(dict(zip(columns, row)))

            return results
        except Exception as e:
            print(f"{Colors.RED}❌ Database query failed: {e}{Colors.RESET}")
            return []

    def verify_user_exists(self, email: str) -> bool:
        """Check if user exists in database"""
        query = "SELECT id FROM users WHERE email = %s"
        results = self.execute_query(query, (email,))
        return len(results) > 0

    def verify_invite_code_exists(self, code: str, active_only: bool = True) -> bool:
        """Check if invite code exists"""
        if active_only:
            query = "SELECT id FROM invite_codes WHERE code = %s AND is_active = true"
        else:
            query = "SELECT id FROM invite_codes WHERE code = %s"
        results = self.execute_query(query, (code,))
        return len(results) > 0

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute an INSERT, UPDATE, or DELETE query and return success status"""
        if not self.connection:
            raise Exception("No database connection")

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()

            # Return number of affected rows
            affected_rows = cursor.rowcount
            print_info(f"DEBUG: Update query affected {affected_rows} rows")

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

    def verify_email_verified(self, email: str) -> bool:
        """Check if user email is verified"""
        query = "SELECT email_verified_at FROM users WHERE email = %s AND email_verified_at IS NOT NULL"
        results = self.execute_query(query, (email,))
        return len(results) > 0

    def verify_user_email_directly(self, email: str) -> bool:
        """Directly verify user email for testing purposes"""
        try:
            query = "UPDATE users SET email_verified_at = NOW() WHERE email = %s RETURNING id"
            results = self.execute_query(query, (email,))
            return len(results) > 0
        except Exception as e:
            print(f"{Colors.RED}Failed to verify user email: {e}{Colors.RESET}")
            return False

    def get_user_id(self, email: str) -> Optional[str]:
        """Get user ID by email"""
        query = "SELECT id FROM users WHERE email = %s"
        results = self.execute_query(query, (email,))
        return results[0]['id'] if results else None

    def check_invite_code_usage(self, code: str) -> Optional[Dict]:
        """Check invite code usage status"""
        query = """
            SELECT ic.code, ic.is_active, ic.used_at, ic.used_by_user_id,
                   u.email as used_by_email
            FROM invite_codes ic
            LEFT JOIN users u ON ic.used_by_user_id = u.id
            WHERE ic.code = %s
        """
        results = self.execute_query(query, (code,))
        return results[0] if results else None

class EmailVerificationHelper:
    """Email verification via Mailcatcher"""

    def __init__(self, mailcatcher_url: str = "http://localhost:1080"):
        self.mailcatcher_url = mailcatcher_url
        self.session = requests.Session()

    def connect_mailcatcher(self) -> bool:
        """Connect to Mailcatcher API"""
        try:
            # Test connection
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

                # Find message to the specified recipient
                for message in messages:
                    recipients = message.get('recipients', [])
                    # Mailcatcher stores recipients as list of strings like ['<email@example.com>']
                    # Remove angle brackets for comparison
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
                print(f"{Colors.RED}❌ No message ID found in email data{Colors.RESET}")
                return None

            # Fetch the actual email content from Mailcatcher
            response = self.session.get(f"{self.mailcatcher_url}/messages/{message_id}.html")

            if response.status_code != 200:
                print(f"{Colors.RED}❌ Failed to fetch email content: {response.status_code}{Colors.RESET}")
                return None

            body = response.text
            body_lower = body.lower()

            # Look for verification link
            if '/verify-email?token=' in body_lower:
                start_index = body_lower.find('/verify-email?token=')
                if start_index != -1:
                    start_index += len('/verify-email?token=')
                    token = body[start_index:]
                    end_index = token.find('"')  # Token ends at quote
                    if end_index != -1:
                        token = token[:end_index]
                    return token

            # Look for token in email body
            if 'token=' in body_lower:
                start_index = body_lower.find('token=')
                if start_index != -1:
                    start_index += len('token=')
                    end_index = body.find('"', start_index)  # Token ends at quote
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

    def post(self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str] = None, auth_token: str = None) -> requests.Response:
        """Make POST request"""
        url = f"{self.base_url}{endpoint}"
        headers = {**self.default_headers}

        if headers:
            headers.update(headers)

        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"

        try:
            start_time = time.time()
            response = self.session.post(url, json=data, headers=headers, timeout=60)
            response_time = time.time() - start_time

            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP request failed: {e}{Colors.RESET}")
            raise e

    def get(self, endpoint: str, headers: Dict[str, str] = None, auth_token: str = None) -> requests.Response:
        """Make GET request"""
        url = f"{self.base_url}{endpoint}"
        headers = {**self.default_headers}

        if headers:
            headers.update(headers)

        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"

        try:
            start_time = time.time()
            response = self.session.get(url, headers=headers, timeout=60)
            response_time = time.time() - start_time

            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP GET request failed: {e}{Colors.RESET}")
            raise e

    def put(self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str] = None, auth_token: str = None) -> requests.Response:
        """Make PUT request"""
        url = f"{self.base_url}{endpoint}"
        headers = {**self.default_headers}

        if headers:
            headers.update(headers)

        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"

        try:
            start_time = time.time()
            response = self.session.put(url, json=data, headers=headers, timeout=60)
            response_time = time.time() - start_time

            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP PUT request failed: {e}{Colors.RESET}")
            raise e

    def delete(self, endpoint: str, headers: Dict[str, str] = None, auth_token: str = None) -> requests.Response:
        """Make DELETE request"""
        url = f"{self.base_url}{endpoint}"
        headers = {**self.default_headers}

        if headers:
            headers.update(headers)

        if auth_token:
            headers['Authorization'] = f"Bearer {auth_token}"

        try:
            start_time = time.time()
            response = self.session.delete(url, headers=headers, timeout=60)
            response_time = time.time() - start_time

            return response, response_time
        except Exception as e:
            print(f"{Colors.RED}❌ HTTP DELETE request failed: {e}{Colors.RESET}")
            raise e

class TokenManager:
    """JWT token management utility"""

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
            # JWT tokens have 3 parts separated by dots
            parts = token.split('.')
            return len(parts) == 3 and all(part.strip() for part in parts)
        except:
            return False

    def is_token_expired(self, token: str) -> bool:
        """Check if JWT token is expired"""
        try:
            decoded = jwt.decode(token, algorithms=["HS256"], options={"verify_signature": False, "verify_exp": False})
            exp_timestamp = decoded.get('exp', 0)
            current_timestamp = int(time.time())
            print_info(f'DEBUG: Token decoded successfully, exp={exp_timestamp}, current={current_timestamp}, expired={exp_timestamp < current_timestamp}')
            return exp_timestamp < current_timestamp
        except Exception as e:
            return True  # If we can't decode, assume expired

class TestReporting:
    """Test result reporting and formatting"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.datetime.now()
        self.end_time = None

    def add_test_result(self, result: TestResult):
        """Add test result to tracking"""
        self.test_results.append(result)

    def set_end_time(self):
        """Mark test completion time"""
        self.end_time = datetime.datetime.now()

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
        print(f"{status_color}⏹ {test_id}: {test_name} - {result.status}")
        print(f"{'='*80}")
        print(f"{'='*80}\n")

    def print_step_result(self, step: TestStep):
        """Print individual step result"""
        status_color = Colors.GREEN if step.is_success() else Colors.RED
        if step.response_time:
            time_info = f" ({step.response_time}ms)"
        else:
            time_info = ""

        print(f"  {step.step_number}. {step.step_name} - {status_color}{step.status}{time_info}")
        if step.message:
            print(f" - {step.message}")

    def print_error_step(self, step: TestStep, error: Exception):
        """Print failed step with error details"""
        print(f"  {step.step_number}. {step_name} - {Colors.RED}FAIL")
        print(f" - Error: {error}")

    def generate_summary_report(self):
        """Generate comprehensive test report"""
        if self.end_time is None:
            self.set_end_time()

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.is_success())
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*80}")
        print(f"{'='*80}")
        print(f"📊 UAT TEST EXECUTION REPORT")
        print(f"{'='*80}")
        print(f"{'='*80}\n")

        print(f"📊 Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Duration: {(self.end_time - self.start_time).total_seconds:.2f} seconds")
        print(f"{'='*80}")
        print(f"📊 Tests Total: {total_tests}")
        print(f"📊 Passed: {passed_tests}")
        print(f"📊 Failed: {failed_tests}")
        print(f"{'='*80}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"{'='*80}\n")

        # Individual test results
        for result in self.test_results:
            status_color = Colors.GREEN if result.is_success() else Colors.RED
            print(f"  {result.test_id}: {result.test_name} - {status_color}{result.status}")

            # Print failed steps for failed tests
            if not result.is_success():
                for step in result.test_steps:
                    if step.status == 'FAIL':
                        print(f"    ❌ Step {step.step_number}: {step.step_name}")

            print(f"{'='*80}")
            print(f"{'='*80}")

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

def wait_for_database_update(db_helper, table: str, condition: str, timeout: int = 10) -> bool:
    """Wait for database update"""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Execute check query
            results = db_helper.execute_query(f"SELECT COUNT(*) FROM {table} WHERE {condition}")
            if results and results[0]['count'] > 0:
                return True

        except:
            pass

        time.sleep(1)

    return False

def format_timestamp(timestamp: Optional[datetime.datetime]) -> str:
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
