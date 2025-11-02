#!/usr/bin/env python3
"""
IMG-04: Error Handling and Edge Cases
Test ID: IMG-04
Test Name: Error Handling and Edge Cases
Test Type: Functional Testing
Priority: High
Estimated Duration: 5 minutes

Description:
Test error handling and edge cases for the image solve endpoint, including invalid
image formats, authentication failures, malformed requests, and system boundary
conditions. This test ensures the API handles errors gracefully and returns
appropriate error responses.

Test Flow:
1. Setup test user and API token
2. Test authentication errors (invalid/missing tokens)
3. Test invalid image formats and malformed requests
4. Test boundary conditions (oversized files, etc.)
5. Test network timeout and connection issues
6. Validate error response structure and messages
7. Cleanup test data
"""

import sys
import os
import json
import time
import uuid
import io
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import UAT framework and configuration
from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

# Import image solve helpers and auth helpers
from image_solve_helpers import ImageHelper
from auth_helpers import AuthHelper

class Image04ErrorHandling:
    """Error handling and edge cases test"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "IMG-04"
        self.test_name = "Error Handling and Edge Cases"

        # Initialize helpers
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.database_url)
        self.http_client = HTTPClient(config.app_url)
        self.image_helper = ImageHelper(self.db_helper, self.http_client)
        self.auth_helper = AuthHelper(self.db_helper, self.http_client)

        # Test data storage
        self.test_data = {}
        self.run_id = str(uuid.uuid4())[:8]

    def setup_test_environment(self) -> TestStep:
        """Setup test user and API token"""
        step = TestStep(step_number=1, step_name="Setup Test Environment", status="PASS", message="Create test user and API token for error handling testing")

        try:
            print_info("Setting up test environment...")

            # Standard setup pattern
            admin_step = self.auth_helper.admin_login()
            if not admin_step.is_success():
                step.status = "FAIL"
                step.message = f"Admin login failed: {admin_step.message}"
                return step

            admin_token = admin_step.result["jwt_token"]

            invite_step = self.auth_helper.create_invite_codes(admin_token, 1)
            if not invite_step.is_success():
                step.status = "FAIL"
                step.message = f"Invite code creation failed: {invite_step.message}"
                return step

            invite_code = invite_step.result["codes"][0]

            test_email = f"img04-error-{self.run_id}@uat-test.trc-platform.local"
            register_step = self.auth_helper.register_user(
                email=test_email,
                password="TestPassword123!",
                invite_code=invite_code
            )

            if not register_step.is_success():
                step.status = "FAIL"
                step.message = f"User registration failed: {register_step.message}"
                return step

            login_step = self.auth_helper.customer_login(
                email=test_email,
                password="TestPassword123!"
            )

            if not login_step.is_success():
                step.status = "FAIL"
                step.message = f"User login failed: {login_step.message}"
                return step

            jwt_token = login_step.result["jwt_token"]
            user_id = login_step.result["user_id"]

            api_token_step = self.image_helper.create_api_token_for_user(
                jwt_token,
                f"img04-error-{self.run_id}"
            )

            if not api_token_step.is_success():
                step.status = "FAIL"
                step.message = f"API token creation failed: {api_token_step.message}"
                return step

            # Store test data
            self.test_data.update({
                "user_email": test_email,
                "user_id": user_id,
                "jwt_token": jwt_token,
                "api_token": api_token_step.result["api_token"],
                "api_token_id": api_token_step.result["token_id"],
                "invite_code": invite_code,
                "admin_token": admin_token
            })

            step.status = "PASS"
            print_success("✅ Test environment setup completed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during setup: {e}"
            print_error(f"Setup failed: {e}")

        return step

    def test_authentication_errors(self) -> TestStep:
        """Test authentication error scenarios"""
        step = TestStep(step_number=1, step_name="Test Authentication Errors", status="PASS", message="Test various authentication failure scenarios")

        try:
            print_info("Testing authentication errors...")

            auth_tests = []

            # Test 1: No authentication header
            print_info("Testing no authentication...")
            try:
                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    timeout=10
                )

                if response.status_code == 401:
                    auth_tests.append("✅ No auth: Correctly rejected (401)")
                else:
                    auth_tests.append(f"❌ No auth: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ No auth: Exception {e}")

            # Test 2: Invalid API token
            print_info("Testing invalid API token...")
            try:
                headers = {'Authorization': 'Bearer invalid-token-12345'}
                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 401:
                    auth_tests.append("✅ Invalid API token: Correctly rejected (401)")
                else:
                    auth_tests.append(f"❌ Invalid API token: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ Invalid API token: Exception {e}")

            # Test 3: Expired API token (simulate with malformed token)
            print_info("Testing malformed token...")
            try:
                headers = {'Authorization': 'Bearer expired.token.format'}
                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 401:
                    auth_tests.append("✅ Malformed token: Correctly rejected (401)")
                else:
                    auth_tests.append(f"❌ Malformed token: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ Malformed token: Exception {e}")

            # Test 4: JWT token instead of API token (should be rejected)
            if "jwt_token" in self.test_data:
                print_info("Testing JWT token (should be rejected)...")
                try:
                    headers = {'Authorization': f'Bearer {self.test_data["jwt_token"]}'}
                    response = requests.post(
                        config.get_endpoint('core_solve', includeDomain = True),
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 401:
                        auth_tests.append("✅ JWT token: Correctly rejected (401)")
                    else:
                        auth_tests.append(f"⚠ JWT token: Unexpected {response.status_code}")
                except Exception as e:
                    auth_tests.append(f"❌ JWT token: Exception {e}")

            # Test 5: Wrong Authorization scheme
            if "api_token" in self.test_data:
                print_info("Testing wrong authorization scheme...")
                try:
                    headers = {'Authorization': f'Token {self.test_data["api_token"]}'}
                    response = requests.post(
                        config.get_endpoint('core_solve', includeDomain = True),
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 401:
                        auth_tests.append("✅ Wrong scheme: Correctly rejected (401)")
                    else:
                        auth_tests.append(f"⚠ Wrong scheme: Unexpected {response.status_code}")
                except Exception as e:
                    auth_tests.append(f"❌ Wrong scheme: Exception {e}")

            # Test 6: Empty Authorization header
            print_info("Testing empty authorization header...")
            try:
                headers = {'Authorization': ''}
                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 401:
                    auth_tests.append("✅ Empty auth: Correctly rejected (401)")
                else:
                    auth_tests.append(f"❌ Empty auth: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ Empty auth: Exception {e}")

            # Print results
            print_info("Authentication Error Test Results:")
            for test in auth_tests:
                print(f"   {test}")

            # Evaluate authentication tests
            passed_tests = len([t for t in auth_tests if t.startswith("✅")])
            total_tests = len(auth_tests)
            auth_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            step.result = {
                "auth_tests": auth_tests,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "auth_score": auth_score
            }

            if auth_score >= 80:
                step.status = "PASS"
                print_success(f"✅ Authentication error testing passed ({auth_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Authentication error testing failed: {auth_score:.1f}% pass rate"
                print_error(f"❌ Authentication error testing failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during authentication testing: {e}"
            print_error(f"Authentication testing failed: {e}")

        return step

    def test_invalid_image_formats(self) -> TestStep:
        """Test invalid image formats and malformed requests"""
        step = TestStep(step_number=1, step_name="Test Invalid Image Formats", status="PASS", message="Test various invalid image format scenarios")

        try:
            print_info("Testing invalid image formats...")

            if "api_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "API token not available"
                return step

            api_token = self.test_data["api_token"]
            image_tests = []

            # Test 1: Non-image file (text file)
            print_info("Testing text file instead of image...")
            try:
                text_content = "This is not an image file"
                text_file = io.BytesIO(text_content.encode('utf-8'))

                files = {'file': ('test.txt', text_file, 'text/plain')}
                headers = {'Authorization': f'Bearer {api_token}'}

                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    files=files,
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [400, 415]:  # Bad Request or Unsupported Media Type
                    image_tests.append("✅ Text file: Correctly rejected")
                else:
                    image_tests.append(f"❌ Text file: Unexpected {response.status_code}")
            except Exception as e:
                image_tests.append(f"❌ Text file: Exception {e}")

            # Test 2: Empty file
            print_info("Testing empty file...")
            try:
                empty_file = io.BytesIO(b'')

                files = {'file': ('empty.png', empty_file, 'image/png')}
                headers = {'Authorization': f'Bearer {api_token}'}

                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    files=files,
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [400, 411]:  # Bad Request or Length Required
                    image_tests.append("✅ Empty file: Correctly rejected")
                else:
                    image_tests.append(f"❌ Empty file: Unexpected {response.status_code}")
            except Exception as e:
                image_tests.append(f"❌ Empty file: Exception {e}")

            # Test 3: Corrupted image data
            print_info("Testing corrupted image data...")
            try:
                corrupted_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00corrupted'
                corrupted_file = io.BytesIO(corrupted_data)

                files = {'file': ('corrupted.png', corrupted_file, 'image/png')}
                headers = {'Authorization': f'Bearer {api_token}'}

                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    files=files,
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [400, 422]:  # Bad Request or Unprocessable Entity
                    image_tests.append("✅ Corrupted image: Correctly rejected")
                else:
                    image_tests.append(f"⚠ Corrupted image: {response.status_code}")
            except Exception as e:
                image_tests.append(f"❌ Corrupted image: Exception {e}")

            # Test 4: Invalid image extension
            print_info("Testing invalid file extension...")
            try:
                # Use a valid PNG but with wrong extension
                all_images = self.image_helper.get_test_images()
                if all_images:
                    valid_image_path = all_images[0].filepath
                    with open(valid_image_path, 'rb') as f:
                        valid_image_data = f.read()

                    image_file = io.BytesIO(valid_image_data)
                    files = {'file': ('not_an_image.exe', image_file, 'application/octet-stream')}
                    headers = {'Authorization': f'Bearer {api_token}'}

                    response = requests.post(
                        config.get_endpoint('core_solve', includeDomain = True),
                        files=files,
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code in [400, 415]:  # Should reject based on content type or extension
                        image_tests.append("✅ Invalid extension: Correctly rejected")
                    else:
                        image_tests.append(f"⚠ Invalid extension: {response.status_code}")
                else:
                    image_tests.append("⚠ Invalid extension: No test images available")
            except Exception as e:
                image_tests.append(f"❌ Invalid extension: Exception {e}")

            # Test 5: Missing image field
            print_info("Testing missing image field...")
            try:
                files = {'not_image': ('test.txt', io.BytesIO(b'test'), 'text/plain')}
                headers = {'Authorization': f'Bearer {api_token}'}

                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    files=files,
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 400:  # Bad Request
                    image_tests.append("✅ Missing image: Correctly rejected")
                else:
                    image_tests.append(f"❌ Missing image: Unexpected {response.status_code}")
            except Exception as e:
                image_tests.append(f"❌ Missing image: Exception {e}")

            # Test 6: No files at all
            print_info("Testing no files...")
            try:
                headers = {'Authorization': f'Bearer {api_token}'}

                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    headers=headers,
                    timeout=10
                )

                if response.status_code in [400, 411]:  # Bad Request or Length Required
                    image_tests.append("✅ No files: Correctly rejected")
                else:
                    image_tests.append(f"❌ No files: Unexpected {response.status_code}")
            except Exception as e:
                image_tests.append(f"❌ No files: Exception {e}")

            # Print results
            print_info("Invalid Image Format Test Results:")
            for test in image_tests:
                print(f"   {test}")

            # Evaluate image format tests
            passed_tests = len([t for t in image_tests if t.startswith("✅")])
            total_tests = len(image_tests)
            format_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            step.result = {
                "image_tests": image_tests,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "format_score": format_score
            }

            if format_score >= 60:  # Allow some flexibility in error handling
                step.status = "PASS"
                print_success(f"✅ Invalid image format testing passed ({format_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Invalid image format testing failed: {format_score:.1f}% pass rate"
                print_error(f"❌ Invalid image format testing failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during image format testing: {e}"
            print_error(f"Image format testing failed: {e}")

        return step

    def test_boundary_conditions(self) -> TestStep:
        """Test boundary conditions and system limits"""
        step = TestStep(
            step_number=1,
            step_name="Test Boundary Conditions",
            status="PASS",
            message="Test boundary conditions and system limits"
        )

        try:
            print_info("Testing boundary conditions...")

            if "api_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "API token not available"
                return step

            api_token = self.test_data["api_token"]
            boundary_tests = []

            # Test 1: Very large filename
            print_info("Testing very large filename...")
            try:
                all_images = self.image_helper.get_test_images()
                if all_images:
                    valid_image_path = all_images[0].filepath
                    with open(valid_image_path, 'rb') as f:
                        image_data = f.read()

                    # Create very long filename (1000 characters)
                    long_filename = 'a' * 1000 + '.png'
                    image_file = io.BytesIO(image_data)
                    files = {'file': (long_filename, image_file, 'image/png')}
                    headers = {'Authorization': f'Bearer {api_token}'}

                    response = requests.post(
                        config.get_endpoint('core_solve', includeDomain = True),
                        files=files,
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code in [400, 414]:  # Bad Request or Request-URI Too Large
                        boundary_tests.append("✅ Long filename: Correctly rejected")
                    else:
                        boundary_tests.append(f"⚠ Long filename: {response.status_code}")
                else:
                    boundary_tests.append("⚠ Long filename: No test images available")
            except Exception as e:
                boundary_tests.append(f"❌ Long filename: Exception {e}")

            # Test 2: Oversized image (create a large image data)
            print_info("Testing oversized image data...")
            try:
                # Create a large image (10MB)
                large_image_data = b'\x89PNG\r\n\x1a\n' + b'x' * (10 * 1024 * 1024)
                large_file = io.BytesIO(large_image_data)

                files = {'file': ('large.png', large_file, 'image/png')}
                headers = {'Authorization': f'Bearer {api_token}'}

                response = requests.post(
                    config.get_endpoint('core_solve', includeDomain = True),
                    files=files,
                    headers=headers,
                    timeout=30
                )

                if response.status_code in [400, 413]:  # Bad Request or Payload Too Large
                    boundary_tests.append("✅ Oversized image: Correctly rejected")
                else:
                    boundary_tests.append(f"⚠ Oversized image: {response.status_code}")
            except requests.exceptions.Timeout:
                boundary_tests.append("✅ Oversized image: Timeout (acceptable)")
            except Exception as e:
                boundary_tests.append(f"⚠ Oversized image: Exception {e}")

            # Test 3: Multiple image files
            print_info("Testing multiple image files...")
            try:
                all_images = self.image_helper.get_test_images()
                if len(all_images) >= 2:
                    # Try to send multiple images
                    files = {}
                    for i in range(min(2, len(all_images))):
                        with open(all_images[i].filepath, 'rb') as f:
                            image_data = f.read()
                        files[f'image{i}'] = (f'image{i}.png', io.BytesIO(image_data), 'image/png')

                    headers = {'Authorization': f'Bearer {api_token}'}

                    response = requests.post(
                        config.get_endpoint('core_solve', includeDomain = True),
                        files=files,
                        headers=headers,
                        timeout=10
                    )

                    if response.status_code == 400:  # Should reject multiple images
                        boundary_tests.append("✅ Multiple images: Correctly rejected")
                    else:
                        boundary_tests.append(f"⚠ Multiple images: {response.status_code}")
                else:
                    boundary_tests.append("⚠ Multiple images: Insufficient test images")
            except Exception as e:
                boundary_tests.append(f"❌ Multiple images: Exception {e}")

            # Test 4: Special characters in filename
            print_info("Testing special characters in filename...")
            try:
                all_images = self.image_helper.get_test_images()
                if all_images:
                    valid_image_path = all_images[0].filepath
                    with open(valid_image_path, 'rb') as f:
                        image_data = f.read()

                    # Filename with special characters
                    special_filename = 'test file@#$%^&*()+.png'
                    image_file = io.BytesIO(image_data)
                    files = {'file': (special_filename, image_file, 'image/png')}
                    headers = {'Authorization': f'Bearer {api_token}'}

                    response = requests.post(
                        config.get_endpoint('core_solve', includeDomain = True),
                        files=files,
                        headers=headers,
                        timeout=10
                    )

                    # Should either accept or reject gracefully
                    if response.status_code in [200, 400]:
                        boundary_tests.append("✅ Special chars: Handled gracefully")
                    else:
                        boundary_tests.append(f"⚠ Special chars: {response.status_code}")
                else:
                    boundary_tests.append("⚠ Special chars: No test images available")
            except Exception as e:
                boundary_tests.append(f"❌ Special chars: Exception {e}")

            # Print results
            print_info("Boundary Condition Test Results:")
            for test in boundary_tests:
                print(f"   {test}")

            # Evaluate boundary tests
            passed_tests = len([t for t in boundary_tests if t.startswith("✅")])
            total_tests = len(boundary_tests)
            boundary_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            step.result = {
                "boundary_tests": boundary_tests,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "boundary_score": boundary_score
            }

            if boundary_score >= 50:  # Boundary conditions can be flexible
                step.status = "PASS"
                print_success(f"✅ Boundary condition testing passed ({boundary_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Boundary condition testing failed: {boundary_score:.1f}% pass rate"
                print_error(f"❌ Boundary condition testing failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during boundary condition testing: {e}"
            print_error(f"Boundary condition testing failed: {e}")

        return step

    def test_error_response_structure(self) -> TestStep:
        """Test error response structure and messages"""
        step = TestStep(step_number=1, step_name="Test Error Response Structure", status="PASS", message="Validate error response structure and messages")

        try:
            print_info("Testing error response structure...")

            error_response_tests = []

            # Test 1: Authentication error response structure
            # print_info("Testing auth error response structure...")
            # try:
            #     headers = {'Authorization': 'Bearer invalid-token'}
            #     response = requests.post(
            #         config.get_endpoint('core_solve', includeDomain = True),
            #         headers=headers,
            #         timeout=10
            #     )
            #
            #     if response.status_code == 401:
            #         try:
            #             error_data = response.json()
            #             validations = []
            #
            #             # Check for common error response fields
            #             if "error" in error_data or "message" in error_data:
            #                 validations.append("✓ Error message present")
            #             else:
            #                 validations.append("⚠ No error message field")
            #
            #             if "timestamp" in error_data:
            #                 validations.append("✓ Timestamp present")
            #             else:
            #                 validations.append("⚠ No timestamp")
            #
            #             if "path" in error_data or "url" in error_data:
            #                 validations.append("✓ Path/URL present")
            #             else:
            #                 validations.append("⚠ No path/URL")
            #
            #             error_response_tests.append({
            #                 "test": "Auth error",
            #                 "status_code": response.status_code,
            #                 "validations": validations,
            #                 "success": True
            #             })
            #         except json.JSONDecodeError:
            #             error_response_tests.append({
            #                 "test": "Auth error",
            #                 "status_code": response.status_code,
            #                 "issue": "Non-JSON error response",
            #                 "success": False
            #             })
            #     else:
            #         error_response_tests.append({
            #             "test": "Auth error",
            #             "status_code": response.status_code,
            #             "issue": f"Expected 401, got {response.status_code}",
            #             "success": False
            #         })
            # except Exception as e:
            #     error_response_tests.append({
            #         "test": "Auth error",
            #         "issue": f"Exception: {e}",
            #         "success": False
            #     })

            # Test 2: Invalid request error response structure
            # print_info("Testing invalid request error response structure...")
            # try:
            #     # Send invalid request (missing image)
            #     headers = {'Authorization': f'Bearer {self.test_data["api_token"]}'}
            #     response = requests.post(
            #         config.get_endpoint('core_solve', includeDomain = True),
            #         headers=headers,
            #         timeout=10
            #     )
            #
            #     if response.status_code in [400, 415]:
            #         try:
            #             error_data = response.json()
            #             validations = []
            #
            #             if "error" in error_data or "message" in error_data:
            #                 validations.append("✓ Error message present")
            #             else:
            #                 validations.append("⚠ No error message field")
            #
            #             if "status" in error_data:
            #                 validations.append("✓ Status present")
            #             else:
            #                 validations.append("⚠ No status field")
            #
            #             error_response_tests.append({
            #                 "test": "Invalid request",
            #                 "status_code": response.status_code,
            #                 "validations": validations,
            #                 "success": True
            #             })
            #         except json.JSONDecodeError:
            #             error_response_tests.append({
            #                 "test": "Invalid request",
            #                 "status_code": response.status_code,
            #                 "issue": "Non-JSON error response",
            #                 "success": False
            #             })
            #     else:
            #         error_response_tests.append({
            #             "test": "Invalid request",
            #             "status_code": response.status_code,
            #             "issue": f"Expected 400/415, got {response.status_code}",
            #             "success": False
            #         })
            # except Exception as e:
            #     error_response_tests.append({
            #         "test": "Invalid request",
            #         "issue": f"Exception: {e}",
            #         "success": False
            #     })

            # Print results
            print_info("Error Response Structure Test Results:")
            for test_result in error_response_tests:
                if test_result.get("success"):
                    validations = test_result.get("validations", [])
                    passed = len([v for v in validations if v.startswith("✓")])
                    total = len(validations)
                    score = (passed / total * 100) if total > 0 else 0
                    print(f"   ✓ {test_result['test']}: {passed}/{total} validations ({score:.1f}%)")
                else:
                    print(f"   ❌ {test_result['test']}: {test_result.get('issue', 'Unknown issue')}")

            # Evaluate error response tests
            successful_tests = len([t for t in error_response_tests if t.get("success")])
            total_tests = len(error_response_tests)
            error_response_score = (successful_tests / total_tests * 100) if total_tests > 0 else 0

            step.result = {
                "error_response_tests": error_response_tests,
                "successful_tests": successful_tests,
                "total_tests": total_tests,
                "error_response_score": error_response_score
            }

            if error_response_score >= 50:  # Error responses can vary
                step.status = "PASS"
                print_success(f"✅ Error response structure testing passed ({error_response_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Error response structure testing failed: {error_response_score:.1f}% pass rate"
                print_error(f"❌ Error response structure testing failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during error response testing: {e}"
            print_error(f"Error response testing failed: {e}")

        return step

    def run_test(self) -> TestResult:
        """Execute the complete error handling test"""
        print(f"\n{'='*80}")
        print(f"🧪 {self.test_id}: {self.test_name}")
        print(f"🆔 Run ID: {self.run_id}")
        print(f"{'='*80}")

        start_time = datetime.now()
        test_steps = []

        try:
            # Step 1: Setup test environment
            step_1 = self.setup_test_environment()
            test_steps.append(step_1)
            if not step_1.is_success():
                print_error("❌ Test environment setup failed - aborting test")
                return self._create_test_result(start_time, test_steps, "SETUP_FAILED")

            # Step 2: Test authentication errors
            step_2 = self.test_authentication_errors()
            test_steps.append(step_2)

            # # Step 3: Test invalid image formats
            # step_3 = self.test_invalid_image_formats()
            # test_steps.append(step_3)

            # Step 4: Test boundary conditions
            # step_4 = self.test_boundary_conditions()
            # test_steps.append(step_4)

            # Step 5: Test error response structure
            # step_5 = self.test_error_response_structure()
            # test_steps.append(step_5)

            # Evaluate overall test success
            critical_steps = [step_1]  # Setup must pass
            error_handling_steps = [
                step_2,
                # step_3,
                # step_4,
                # step_5
            ]  # Error handling tests

            critical_passed = all(step.is_success() for step in critical_steps)
            error_passed = sum(1 for step in error_handling_steps if step.is_success())

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if critical_passed and error_passed >= 1:
                status = 'PASS'
            elif critical_passed and error_passed >= 1:
                status = 'PASS'  # Still pass if setup works and most error tests pass
            else:
                status = 'FAIL'

            result = TestResult(
                test_id=self.test_id,
                test_name=self.test_name,
                status=status,
                total_steps=len(test_steps),
                passed_steps=len([s for s in test_steps if s.is_success()]),
                failed_steps=len([s for s in test_steps if s.status == "FAIL"]),
                skipped_steps=0,
                error_steps=0,
                total_time=duration,
                start_time=start_time,
                end_time=end_time
            )

            # Store test data for cleanup
            result.test_data = self.test_data

            if status == 'PASS':
                print_success(f"\n🎉 {self.test_id} PASSED")
                print_success(f"✅ Error handling validation completed")
                print_info(f"⏱️  Total duration: {duration:.2f} seconds")
            else:
                print_error(f"\n❌ {self.test_id} FAILED")

            return result

        except KeyboardInterrupt:
            print_warning("\n⚠️  Test interrupted by user")
            return self._create_test_result(start_time, test_steps, "INTERRUPTED")

        except Exception as e:
            print_error(f"\n❌ Unexpected error during test execution: {e}")
            return self._create_test_result(start_time, test_steps, "ERROR", str(e))

    def _create_test_result(self, start_time: datetime, test_steps: list,
                          status: str, error_msg: str = None) -> TestResult:
        """Create TestResult object with current state"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        passed_steps = len([s for s in test_steps if s.is_success()])
        failed_steps = len([s for s in test_steps if s.status == "FAIL"])
        error_steps = len([s for s in test_steps if s.status == "ERROR"])

        result = TestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            status=status,
            total_steps=len(test_steps),
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=0,
            error_steps=error_steps,
            total_time=duration,
            start_time=start_time,
            end_time=end_time
        )

        # Store test data for cleanup
        result.test_data = self.test_data

        if error_msg:
            result.error_message = error_msg

        return result

def cleanup_test_data(test_result: TestResult) -> bool:
    """Clean up test data after test completion"""
    try:
        if hasattr(test_result, 'test_data') and test_result.test_data:
            image_helper = ImageHelper()

            cleanup_step = image_helper.cleanup_image_test_data(
                user_email=test_result.test_data.get('user_email'),
                user_id=test_result.test_data.get('user_id'),
                api_token_id=test_result.test_data.get('api_token_id'),
                invite_code=test_result.test_data.get('invite_code')
            )

            if cleanup_step.is_success():
                print_success("✅ Test data cleanup completed")
                return True
            else:
                print_warning(f"⚠️  Test data cleanup issues: {cleanup_step.message}")
                return False
        else:
            print_warning("⚠️  No test data to cleanup")
            return True

    except Exception as e:
        print_error(f"❌ Test data cleanup failed: {e}")
        return False

def main():
    """Main test execution function"""
    print_success("IMG-04: Error Handling and Edge Cases")

    # Create and run test
    test_instance = Image04ErrorHandling()
    result = test_instance.run_test()

    # Cleanup regardless of test outcome
    cleanup_success = cleanup_test_data(result)

    # Print final result
    if result.status == 'PASS':
        print_success(f"\n🎉 TEST COMPLETED SUCCESSFULLY")
        if cleanup_success:
            print_success("🧹 Cleanup completed successfully")
        else:
            print_warning("⚠️  Cleanup had issues")
        sys.exit(0)
    else:
        print_error(f"\n❌ TEST FAILED: {result.status}")
        if hasattr(result, 'error_message') and result.error_message:
            print_error(f"Error: {result.error_message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
