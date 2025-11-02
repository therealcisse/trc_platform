#!/usr/bin/env python3
"""
IMG-02: Basic Image Solve Functionality
Test ID: IMG-02
Test Name: Basic Image Solve Functionality
Test Type: Functional Testing
Priority: High
Estimated Duration: 5 minutes

Description:
Test basic image solving functionality using API token authentication.
This test validates the core image solve workflow by processing several sample
images and validating the responses against expected answers from filenames.

Test Flow:
1. Setup test user and API token (reuse IMG-01 pattern)
2. Process 3-5 sample images using API token authentication
3. Validate each response structure and expected answers
4. Verify proper error handling and response formatting
5. Cleanup test data
"""

import sys
import os
import json
import time
import uuid
import random
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

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

class Image02BasicSolve:
    """Basic image solve functionality test"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "IMG-02"
        self.test_name = "Basic Image Solve Functionality"

        # Initialize helpers
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.database_url)
        self.http_client = HTTPClient(config.app_url)
        self.image_helper = ImageHelper(self.db_helper, self.http_client)
        self.auth_helper = AuthHelper(self.db_helper, self.http_client)

        # Test data storage
        self.test_data = {}
        self.run_id = str(uuid.uuid4())[:8]

        # Select a few sample images for basic testing
        self.sample_images = [
            "001_a8.png",    # Simple case
            "002_a14.png",   # Different difficulty
            "003_a7.png",    # Another simple case
            "010_a3.png",    # Double-digit result
            "000__a10.png"   # Special case with double underscore
        ]

    def setup_test_environment(self) -> TestStep:
        """Setup test user and API token following IMG-01 pattern"""
        step = TestStep(
            step_number=1,
            step_name="Setup Test Environment",
            status="PASS",
            message="Setting up test environment..."
        )

        try:
            print_info("Setting up test environment...")

            # Step 1: Admin login
            admin_step = self.auth_helper.admin_login()
            if not admin_step.is_success():
                step.status = "FAIL"
                step.message = f"Admin login failed: {admin_step.message}"
                return step

            admin_token = admin_step.result["jwt_token"]

            # Step 2: Create invite code
            invite_step = self.auth_helper.create_invite_codes(admin_token, 1)
            if not invite_step.is_success():
                step.status = "FAIL"
                step.message = f"Invite code creation failed: {invite_step.message}"
                return step

            invite_code = invite_step.result["codes"][0]

            # Step 3: Register test user
            test_email = f"img02-basic-{self.run_id}@uat-test.trc-platform.local"
            register_step = self.auth_helper.register_user(
                email=test_email,
                password="TestPassword123!",
                invite_code=invite_code
            )

            if not register_step.is_success():
                step.status = "FAIL"
                step.message = f"User registration failed: {register_step.message}"
                return step

            # Step 4: User login
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

            # Step 5: Create API token
            api_token_step = self.image_helper.create_api_token_for_user(
                jwt_token,
                f"img02-basic-{self.run_id}"
            )

            if not api_token_step.is_success():
                step.status = "FAIL"
                step.message = f"API token creation failed: {api_token_step.message}"
                return step

            api_token = api_token_step.result["api_token"]
            api_token_id = api_token_step.result["token_id"]

            # Store test data
            self.test_data.update({
                "user_email": test_email,
                "user_id": user_id,
                "jwt_token": jwt_token,
                "api_token": api_token,
                "api_token_id": api_token_id,
                "invite_code": invite_code,
                "admin_token": admin_token
            })

            step.result = {
                "user_email": test_email,
                "user_id": user_id,
                "api_token_name": f"img02-basic-{self.run_id}",
                "setup_completed": True
            }

            step.status = "PASS"
            print_success("✅ Test environment setup completed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during setup: {e}"
            print_error(f"Setup failed: {e}")

        return step

    def test_sample_images(self) -> TestStep:
        """Test solving sample images and validate responses"""
        step = TestStep(
            step_number=2,
            step_name="Test Sample Images",
            status="PASS",
            message="Testing sample images..."
        )

        try:
            print_info("Testing sample images...")

            if "api_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "API token not available"
                return step

            api_token = self.test_data["api_token"]
            image_results = []

            # Get available test images
            all_images = self.image_helper.get_test_images()
            if not all_images:
                step.status = "FAIL"
                step.message = "No test images found"
                return step

            # Filter to our sample images (check if they exist)
            available_sample_images = []
            for sample_name in self.sample_images:
                for img in all_images:
                    if img.filename == sample_name:
                        available_sample_images.append(img)
                        break

            if not available_sample_images:
                # Fallback: use any 3-5 available images
                available_sample_images = all_images[:min(5, len(all_images))]
                print_warning(f"Sample images not found, using {len(available_sample_images)} available images")

            print_info(f"Testing {len(available_sample_images)} images...")

            # Test each image
            for image_data in available_sample_images:
                print_info(f"Processing image: {image_data.filename} (expected: {image_data.expected_answer}) using token {api_token}")

                # Upload and solve image
                solve_step = self.image_helper.upload_and_solve(
                    image_data.filepath,
                    api_token
                )

                if not solve_step.is_success():
                    print_error(f"❌ Failed to solve {image_data.filename}: {solve_step.message}")
                    image_results.append({
                        "filename": image_data.filename,
                        "expected_answer": image_data.expected_answer,
                        "success": False,
                        "error": solve_step.message
                    })
                    continue

                solve_response = solve_step.result["solve_response"]

                # Validate response against expected answer
                validation_step = self.image_helper.validate_solve_response(
                    solve_response,
                    image_data.expected_answer
                )

                result_data = {
                    "filename": image_data.filename,
                    "expected_answer": image_data.expected_answer,
                    "actual_result": solve_response.result,
                    "request_id": solve_response.request_id,
                    "duration_ms": solve_response.duration_ms,
                    "response_time": solve_response.response_time,
                    "success": validation_step.is_success(),
                    "validations": validation_step.result.get("validations", []) if validation_step.result else []
                }

                if validation_step.is_success():
                    print_success(f"✅ {image_data.filename}: {image_data.expected_answer} ✓")
                else:
                    print_error(f"❌ {image_data.filename}: expected {image_data.expected_answer}, got {solve_response.result}")

                image_results.append(result_data)

            # Calculate success statistics
            successful_tests = len([r for r in image_results if r["success"]])
            total_tests = len(image_results)
            success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0

            print_info(f"Results: {successful_tests}/{total_tests} images solved correctly ({success_rate:.1f}%)")

            # Store results for later analysis
            self.test_data["image_results"] = image_results

            step.result = {
                "total_images_tested": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "image_results": image_results
            }

            # Require at least 60% success rate for basic functionality test
            if success_rate >= 60:
                step.status = "PASS"
                print_success("✅ Sample image testing completed successfully")
            else:
                step.status = "FAIL"
                step.message = f"Low success rate: {success_rate:.1f}% (expected at least 60%)"
                print_error(f"❌ Low success rate: {success_rate:.1f}%")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during image testing: {e}"
            print_error(f"Image testing failed: {e}")

        return step

    def test_response_structure(self) -> TestStep:
        """Test response structure and timing data"""
        step = TestStep(
            step_number=3,
            step_name="Test Response Structure",
            status="PASS",
            message="Testing response structure..."
        )

        try:
            print_info("Testing response structure...")

            if "image_results" not in self.test_data:
                step.status = "FAIL"
                step.message = "No image results available for structure validation"
                return step

            image_results = self.test_data["image_results"]
            successful_results = [r for r in image_results if r["success"]]

            if not successful_results:
                step.status = "FAIL"
                step.message = "No successful image results to validate"
                return step

            structure_validations = []
            timing_validations = []

            # Validate response structure for successful results
            for result in successful_results[:3]:  # Check first 3 successful results
                validations = result.get("validations", [])
                structure_validations.extend(validations)

                # Additional timing-specific validations
                if result.get("duration_ms", 0) > 0:
                    timing_validations.append(f"✓ {result['filename']}: Valid duration ({result['duration_ms']}ms)")
                else:
                    timing_validations.append(f"⚠ {result['filename']}: Zero or missing duration")

                if result.get("response_time", 0) > 0:
                    timing_validations.append(f"✓ {result['filename']}: Valid response time ({result['response_time']:.2f}s)")
                else:
                    timing_validations.append(f"⚠ {result['filename']}: Zero or missing response time")

                if result.get("request_id"):
                    timing_validations.append(f"✓ {result['filename']}: Request ID present ({result['request_id'][:8]}...)")
                else:
                    timing_validations.append(f"❌ {result['filename']}: Missing request ID")

            # Print validation results
            print_info("Response Structure Validations:")
            for validation in structure_validations:
                print(f"   {validation}")

            print_info("\nTiming Data Validations:")
            for validation in timing_validations:
                print(f"   {validation}")

            # Calculate structure validation score
            valid_structures = len([v for v in structure_validations if v.startswith("✓")])
            total_structures = len(structure_validations)
            structure_score = (valid_structures / total_structures * 100) if total_structures > 0 else 0

            valid_timing = len([v for v in timing_validations if v.startswith("✓")])
            total_timing = len(timing_validations)
            timing_score = (valid_timing / total_timing * 100) if total_timing > 0 else 0

            step.result = {
                "structure_validations": structure_validations,
                "timing_validations": timing_validations,
                "structure_score": structure_score,
                "timing_score": timing_score,
                "total_successful_results": len(successful_results)
            }

            # Consider successful if both scores are above 70%
            if structure_score >= 70 and timing_score >= 70:
                step.status = "PASS"
                print_success("✅ Response structure validation completed")
            else:
                step.status = "FAIL"
                step.message = f"Low validation scores - Structure: {structure_score:.1f}%, Timing: {timing_score:.1f}%"
                print_error(f"❌ Response structure validation failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during response structure testing: {e}"
            print_error(f"Response structure testing failed: {e}")

        return step

    def test_api_authentication(self) -> TestStep:
        """Test API token authentication requirements"""
        step = TestStep(
            step_number=4,
            step_name="Test API Authentication",
            status="PASS",
            message="Testing API authentication..."
        )

        try:
            print_info("Testing API authentication...")

            if not self.test_data.get("api_token") or not self.test_data.get("jwt_token"):
                step.status = "FAIL"
                step.message = "Required tokens not available"
                return step

            api_token = self.test_data["api_token"]
            jwt_token = self.test_data["jwt_token"]

            auth_tests = []

            # Test 1: API token authentication (should work)
            print_info("Testing API token authentication...")
            try:
                # Create a simple test image data for authentication test
                test_data = {'image': 'test'}
                headers = {'Authorizaton': f"Bearer {api_token}"}
                response, response_time = self.http_client.post(
                    config.get_endpoint('core_solve'),
                    test_data,
                    headers=headers
                )

                # Should get 400/422 for missing image file, not 401 (auth succeeded)
                if response.status_code in [400, 422]:
                    auth_tests.append("✅ API token authentication: Accepted (400/422 as expected)")
                elif response.status_code == 401:
                    auth_tests.append("❌ API token authentication: Rejected (401)")
                else:
                    auth_tests.append(f"⚠ API token authentication: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ API token authentication: Exception {e}")

            # Test 2: JWT token authentication (should be rejected)
            print_info("Testing JWT token authentication (should be rejected)...")
            try:
                test_data = {'image': 'test'}
                response, response_time = self.http_client.post(
                    config.get_endpoint('core_solve'),
                    test_data,
                    auth_token=jwt_token
                )

                if response.status_code == 401:
                    auth_tests.append("✅ JWT token authentication: Correctly rejected (401)")
                elif response.status_code in [400, 422]:
                    auth_tests.append("⚠ JWT token authentication: Unexpectedly accepted")
                else:
                    auth_tests.append(f"⚠ JWT token authentication: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ JWT token authentication: Exception {e}")

            # Test 3: No authentication (should be rejected)
            print_info("Testing no authentication (should be rejected)...")
            try:
                test_data = {'image': 'test'}
                response, response_time = self.http_client.post(
                    config.get_endpoint('core_solve'),
                    test_data
                )

                if response.status_code == 401:
                    auth_tests.append("✅ No authentication: Correctly rejected (401)")
                else:
                    auth_tests.append(f"⚠ No authentication: Unexpected {response.status_code}")
            except Exception as e:
                auth_tests.append(f"❌ No authentication: Exception {e}")

            # Print results
            print_info("Authentication Test Results:")
            for test in auth_tests:
                print(f"   {test}")

            # Evaluate overall authentication test
            passed_tests = len([t for t in auth_tests if t.startswith("✅")])
            total_tests = len(auth_tests)
            auth_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            step.result = {
                "auth_tests": auth_tests,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "auth_score": auth_score
            }

            # Require at least 66% of auth tests to pass (2 out of 3)
            if auth_score >= 66:
                step.status = "PASS"
                print_success("✅ API authentication testing completed")
            else:
                step.status = "FAIL"
                step.message = f"Authentication test failed: {auth_score:.1f}% pass rate"
                print_error(f"❌ API authentication testing failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during authentication testing: {e}"
            print_error(f"API authentication testing failed: {e}")

        return step

    def run_test(self) -> TestResult:
        """Execute the complete basic image solve test"""
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

            # Step 2: Test sample images
            step_2 = self.test_sample_images()
            test_steps.append(step_2)
            if not step_2.is_success():
                print_warning("⚠️ Sample image testing had issues, but continuing...")

            # Step 3: Test response structure
            step_3 = self.test_response_structure()
            test_steps.append(step_3)
            if not step_3.is_success():
                print_warning("⚠️ Response structure testing had issues, but continuing...")

            # Step 4: Test API authentication
            step_4 = self.test_api_authentication()
            test_steps.append(step_4)
            if not step_4.is_success():
                print_warning("⚠️ API authentication testing had issues, but continuing...")

            # Evaluate overall test success
            critical_steps = [step_1, step_2]  # These must pass
            optional_steps = [step_3, step_4]  # These can have issues

            critical_passed = all(step.is_success() for step in critical_steps)
            optional_passed = sum(1 for step in optional_steps if step.is_success())

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if critical_passed and optional_passed >= 1:
                status = 'PASS'
            elif critical_passed:
                status = 'PASS'  # Still pass if critical steps work
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
                if hasattr(step_2, 'result') and step_2.result:
                    success_rate = step_2.result.get('success_rate', 0)
                    print_success(f"✅ Image solve success rate: {success_rate:.1f}%")
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
        failed_steps = len([s for s in test_steps if not s.is_success() and s.status != 'SKIP'])
        error_steps = len([s for s in test_steps if s.status == 'ERROR'])

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
    print_success("IMG-02: Basic Image Solve Functionality")

    # Create and run test
    test_instance = Image02BasicSolve()
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
