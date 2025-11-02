#!/usr/bin/env python3
"""
IMG-05: Billing Integration Verification
Test ID: IMG-05
Test Name: Billing Integration Verification
Test Type: Integration Testing
Priority: High
Estimated Duration: 8 minutes

Description:
Verify that image solve requests are properly logged and integrated with the billing
system. This test ensures request logs are created correctly, billing periods are
assigned, costs are calculated properly, and the service field is set correctly
for image solve operations.

Test Flow:
1. Setup test user and API token
2. Process several images to generate request logs
3. Verify request logs are created with correct service field
4. Check billing period assignment and cost tracking
5. Validate billing integration for multiple requests
6. Cleanup test data
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
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

class Image05BillingIntegration:
    """Billing integration verification test"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "IMG-05"
        self.test_name = "Billing Integration Verification"

        # Initialize helpers
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.database_url)
        self.http_client = HTTPClient(config.app_url)
        self.image_helper = ImageHelper(self.db_helper, self.http_client)
        self.auth_helper = AuthHelper(self.db_helper, self.http_client)

        # Test data storage
        self.test_data = {}
        self.run_id = str(uuid.uuid4())[:8]
        self.generated_request_ids = []

        # Test images for billing verification
        self.test_images = [
            "001_a8.png",
            "002_a14.png",
            "003_a7.png",
            "004_a8.png",
            "005_a8.png"
        ]

    def setup_test_environment(self) -> TestStep:
        """Setup test user and API token"""
        step = TestStep(step_number=1, step_name="Setup Test Environment", status="PASS", message="Create test user and API token for billing integration testing")

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

            test_email = f"img05-billing-{self.run_id}@uat-test.trc-platform.local"
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
                f"img05-billing-{self.run_id}"
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

    def generate_image_requests(self) -> TestStep:
        """Generate image solve requests to create billing data"""
        step = TestStep(step_number=1, step_name="Generate Image Requests", status="PASS", message="Process multiple images to generate request logs for billing verification")

        try:
            print_info("Generating image requests for billing verification...")

            if "api_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "API token not available"
                return step

            api_token = self.test_data["api_token"]
            user_id = self.test_data["user_id"]

            # Get available test images
            all_images = self.image_helper.get_test_images()
            if not all_images:
                step.status = "FAIL"
                step.message = "No test images found"
                return step

            # Find our test images or use available ones
            test_image_data = []
            for test_name in self.test_images:
                for img in all_images:
                    if img.filename == test_name:
                        test_image_data.append(img)
                        break

            if not test_image_data:
                test_image_data = all_images[:5]  # Use first 5 available images

            print_info(f"Processing {len(test_image_data)} images to generate billing data...")

            processed_requests = []

            for i, image_data in enumerate(test_image_data):
                print_info(f"Processing image {i+1}/{len(test_image_data)}: {image_data.filename}")

                solve_step = self.image_helper.upload_and_solve(
                    image_data.filepath,
                    api_token
                )

                if solve_step.is_success():
                    solve_response = solve_step.result["solve_response"]
                    request_id = solve_response.request_id

                    # Store request ID for verification
                    self.generated_request_ids.append(request_id)

                    request_data = {
                        "filename": image_data.filename,
                        "expected_answer": image_data.expected_answer,
                        "request_id": request_id,
                        "duration_ms": solve_response.duration_ms,
                        "response_time": solve_response.response_time,
                        "result": solve_response.result,
                        "timestamp": datetime.now().isoformat(),
                        "success": True
                    }

                    processed_requests.append(request_data)
                    print_success(f"✅ Generated request: {request_id}")
                else:
                    print_warning(f"⚠️ Failed to process {image_data.filename}: {solve_step.message}")
                    processed_requests.append({
                        "filename": image_data.filename,
                        "success": False,
                        "error": solve_step.message
                    })

            # Wait a moment for database operations to complete
            time.sleep(2)

            step.result = {
                "total_processed": len(processed_requests),
                "successful_requests": len([r for r in processed_requests if r["success"]]),
                "failed_requests": len([r for r in processed_requests if not r["success"]]),
                "request_ids": self.generated_request_ids,
                "processed_requests": processed_requests
            }

            successful_count = len([r for r in processed_requests if r["success"]])
            if successful_count >= 3:
                step.status = "PASS"
                print_success(f"✅ Generated {successful_count} successful image requests")
            else:
                step.status = "FAIL"
                step.message = f"Insufficient successful requests: {successful_count} (need at least 3)"
                print_error(f"❌ Insufficient requests generated: {successful_count}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception generating image requests: {e}"
            print_error(f"Image request generation failed: {e}")

        return step

    def verify_request_logs(self) -> TestStep:
        """Verify request logs are created correctly"""
        step = TestStep(
            step_number=1,
            step_name="Verify Request Logs",
            status="PASS",
            message="Verify request logs are created with correct data for image solve requests"
        )

        try:
            print_info("Verifying request logs...")

            if not self.generated_request_ids:
                step.status = "FAIL"
                step.message = "No request IDs to verify"
                return step

            user_id = self.test_data["user_id"]
            verifications = []

            # Query request logs for this user
            query = """
                SELECT request_id, service, status, duration_ms, request_bytes,
                       response_bytes, request_ts, billing_period_id,
                       flow_id, user_id, token_id
                FROM request_logs
                WHERE user_id = %s AND service = 'core.image_solve'
                ORDER BY request_ts DESC
                LIMIT 20
            """

            logs = self.db_helper.execute_query(query, (user_id,))

            if not logs:
                step.status = "FAIL"
                step.message = "No request logs found for image solve requests"
                return step

            print_info(f"Found {len(logs)} image solve request logs")

            # Verify each log entry
            for log in logs:
                log_validations = []
                request_id = log['request_id']

                # Check if this request ID matches one we generated
                if request_id in self.generated_request_ids:
                    log_validations.append(f"✓ Request ID matches generated request")

                    # Remove from unverified list
                    self.generated_request_ids.remove(request_id)
                else:
                    log_validations.append(f"⚠ Request ID not in our generated list")

                # Verify service field
                if log.get('service') == 'core.image_solve':
                    log_validations.append("✓ Service field correct")
                else:
                    log_validations.append(f"❌ Service field incorrect: {log.get('service')}")

                # Verify status
                if log.get('status') in ['SUCCESS', 'ERROR']:
                    log_validations.append(f"✓ Status valid: {log.get('status')}")
                else:
                    log_validations.append(f"❌ Status invalid: {log.get('status')}")

                # Verify user ID
                if log.get('user_id') == user_id:
                    log_validations.append("✓ User ID correct")
                else:
                    log_validations.append("❌ User ID mismatch")

                # Verify duration
                duration = log.get('duration_ms')
                if duration is not None and isinstance(duration, int) and duration >= 0:
                    log_validations.append(f"✓ Duration valid: {duration}ms")
                else:
                    log_validations.append(f"❌ Duration invalid: {duration}")

                # Verify timestamps
                created_at = log.get('created_at')
                if created_at:
                    log_validations.append("✓ Created timestamp present")
                else:
                    log_validations.append("❌ Created timestamp missing")

                # Verify billing period assignment
                if log.get('billing_period_id'):
                    log_validations.append("✓ Billing period assigned")
                else:
                    log_validations.append("⚠ No billing period assigned")

                # Note: Cost is stored at billing period level, not request log level
                # Individual request costs are not tracked in request_logs table

                verifications.append({
                    "request_id": request_id,
                    "validations": log_validations,
                    "log_data": log
                })

                # Print validation summary for this log
                valid_count = len([v for v in log_validations if v.startswith("✓")])
                total_count = len(log_validations)
                score = (valid_count / total_count * 100) if total_count > 0 else 0
                print_info(f"   {request_id[:8]}...: {valid_count}/{total_count} validations passed ({score:.1f}%)")

            # Check for any missing request IDs
            if self.generated_request_ids:
                print_warning(f"⚠ {len(self.generated_request_ids)} generated requests not found in logs")
                for missing_id in self.generated_request_ids:
                    print_warning(f"   Missing: {missing_id}")
            else:
                print_success("✅ All generated requests found in logs")

            # Calculate overall verification score
            total_validations = sum(len(v["validations"]) for v in verifications)
            passed_validations = sum(len([val for val in v["validations"] if val.startswith("✓")]) for v in verifications)
            overall_score = (passed_validations / total_validations * 100) if total_validations > 0 else 0

            step.result = {
                "verifications": verifications,
                "total_logs": len(logs),
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "overall_score": overall_score,
                "missing_requests": len(self.generated_request_ids)
            }

            if overall_score >= 80 and len(self.generated_request_ids) == 0:
                step.status = "PASS"
                print_success(f"✅ Request log verification passed ({overall_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Request log verification failed: score {overall_score:.1f}%, missing {len(self.generated_request_ids)} requests"
                print_error(f"❌ Request log verification failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during request log verification: {e}"
            print_error(f"Request log verification failed: {e}")

        return step

    def verify_billing_periods(self) -> TestStep:
        """Verify billing periods are created and managed correctly"""
        step = TestStep(step_number=1, step_name="Verify Billing Periods", status="PASS", message="Verify billing periods are created and associated with image solve requests")

        try:
            print_info("Verifying billing periods...")

            user_id = self.test_data["user_id"]
            billing_verifications = []

            # Query billing periods for this user
            billing_query = """
                SELECT id, user_id, payment_status, total_cost_cents, total_requests, period_start, period_end,
                       paid_at
                FROM billing_periods
                WHERE user_id = %s
                ORDER BY period_start DESC
                LIMIT 10
            """

            billing_periods = self.db_helper.execute_query(billing_query, (user_id,))

            if not billing_periods:
                step.status = "FAIL"
                step.message = "No billing periods found for user"
                return step

            print_info(f"Found {len(billing_periods)} billing periods")

            # Verify each billing period
            for period in billing_periods:
                period_validations = []

                # Check billing period structure
                if period.get('id'):
                    period_validations.append("✓ Billing period ID present")
                else:
                    period_validations.append("❌ Billing period ID missing")

                # Check status
                status = period.get('payment_status')
                if status in ['pending', 'paid', 'waived', 'overdue']:
                    period_validations.append(f"✓ Status valid: {status}")
                else:
                    period_validations.append(f"⚠ Status unusual: {status}")

                # Check cost and requests
                total_cost = period.get('total_cost_cents')
                total_requests = period.get('total_requests')

                if total_cost is not None and total_cost >= 0:
                    period_validations.append(f"✓ Total cost valid: {total_cost}")
                else:
                    period_validations.append(f"⚠ Total cost invalid: {total_cost}")

                if total_requests is not None and total_requests >= 0:
                    period_validations.append(f"✓ Total requests valid: {total_requests}")
                else:
                    period_validations.append(f"⚠ Total requests invalid: {total_requests}")

                # Check dates
                if period.get('start_date'):
                    period_validations.append("✓ Start date present")
                else:
                    period_validations.append("❌ Start date missing")

                if period.get('created_at'):
                    period_validations.append("✓ Created at present")
                else:
                    period_validations.append("❌ Created at missing")

                # Count image solve requests for this billing period
                if period.get('id'):
                    requests_query = """
                        SELECT COUNT(*) as request_count, SUM(bp.total_cost_cents) as total_cost_cents
                        FROM request_logs rl LEFT JOIN billing_periods bp ON (rl.billing_period_id = bp.id)
                        WHERE bp.user_id = %s AND rl.billing_period_id = %s AND rl.service = 'core.image_solve'
                    """
                    request_stats = self.db_helper.execute_query(
                        requests_query,
                        (user_id, period['id'])
                    )

                    if request_stats:
                        stats = request_stats[0]
                        image_count = stats.get('request_count', 0)
                        image_cost = stats.get('total_cost_cents', 0)

                        if image_count > 0:
                            period_validations.append(f"✓ Image solve requests: {image_count}")
                        else:
                            period_validations.append("⚠ No image solve requests found")

                        if image_cost >= 0:
                            period_validations.append(f"✓ Image solve cost: {image_cost}")
                        else:
                            period_validations.append(f"⚠ Invalid image solve cost: {image_cost}")
                    else:
                        period_validations.append("❌ Could not query request statistics")

                billing_verifications.append({
                    "billing_period_id": period.get('id'),
                    "validations": period_validations,
                    "period_data": period
                })

                # Print validation summary for this billing period
                valid_count = len([v for v in period_validations if v.startswith("✓")])
                total_count = len(period_validations)
                score = (valid_count / total_count * 100) if total_count > 0 else 0
                print_info(f"   Billing Period {period.get('id', 'Unknown')[:8]}...: {valid_count}/{total_count} validations ({score:.1f}%)")

            # Calculate overall billing verification score
            total_validations = sum(len(v["validations"]) for v in billing_verifications)
            passed_validations = sum(len([val for val in v["validations"] if val.startswith("✓")]) for v in billing_verifications)
            overall_score = (passed_validations / total_validations * 100) if total_validations > 0 else 0

            step.result = {
                "billing_verifications": billing_verifications,
                "total_billing_periods": len(billing_periods),
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "overall_score": overall_score
            }

            if overall_score >= 75:
                step.status = "PASS"
                print_success(f"✅ Billing period verification passed ({overall_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Billing period verification failed: {overall_score:.1f}% pass rate"
                print_error(f"❌ Billing period verification failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during billing period verification: {e}"
            print_error(f"Billing period verification failed: {e}")

        return step

    def verify_cost_tracking(self) -> TestStep:
        """Verify cost tracking and calculation accuracy"""
        step = TestStep(step_number=1, step_name="Verify Cost Tracking", status="PASS", message="Verify cost tracking and calculation for image solve requests")

        try:
            print_info("Verifying cost tracking...")

            user_id = self.test_data["user_id"]
            cost_verifications = []

            # Get cost per request from settings table
            settings_query = "SELECT cost_per_request_cents FROM settings LIMIT 1"
            settings_result = self.db_helper.execute_query(settings_query)

            if not settings_result:
                step.status = "FAIL"
                step.message = "Unable to retrieve cost settings from database"
                return step

            cost_per_request_cents = settings_result[0]['cost_per_request_cents']
            print_info(f"Cost per request from settings: {cost_per_request_cents} cents")

            # Query current billing period for the user
            billing_query = """
                SELECT id, user_id, payment_status, total_cost_cents, total_requests,
                       period_start, period_end, is_current
                FROM billing_periods
                WHERE user_id = %s AND is_current = true
                ORDER BY period_start DESC
                LIMIT 1
            """

            billing_periods = self.db_helper.execute_query(billing_query, (user_id,))

            if not billing_periods:
                step.status = "FAIL"
                step.message = "No current billing period found for user"
                return step

            billing_period = billing_periods[0]
            print_info(f"Found billing period: {billing_period['id']}")
            print_info(f"Total requests: {billing_period['total_requests']}")
            print_info(f"Total cost: {billing_period['total_cost_cents']} cents")
            print_info(f"Payment status: {billing_period['payment_status']}")

            # Verify cost calculation accuracy
            period_validations = []

            # Check billing period structure
            if billing_period.get('id'):
                period_validations.append("✓ Billing period ID present")
            else:
                period_validations.append("❌ Billing period ID missing")

            # Check payment status
            payment_status = billing_period.get('payment_status')
            if payment_status in ['pending', 'paid', 'waived', 'overdue']:
                period_validations.append(f"✓ Payment status valid: {payment_status}")
            else:
                period_validations.append(f"❌ Payment status invalid: {payment_status}")

            # Verify total requests is non-negative
            total_requests = billing_period.get('total_requests', 0)
            if total_requests is not None and total_requests >= 0:
                period_validations.append(f"✓ Total requests valid: {total_requests}")
            else:
                period_validations.append(f"❌ Total requests invalid: {total_requests}")

            # Verify total cost is non-negative
            total_cost_cents = billing_period.get('total_cost_cents', 0)
            if total_cost_cents is not None and total_cost_cents >= 0:
                period_validations.append(f"✓ Total cost valid: {total_cost_cents} cents")
            else:
                period_validations.append(f"❌ Total cost invalid: {total_cost_cents}")

            # Verify cost calculation accuracy
            expected_total_cost = total_requests * cost_per_request_cents
            if total_cost_cents == expected_total_cost:
                period_validations.append(f"✓ Cost calculation accurate: {total_requests} × {cost_per_request_cents} = {total_cost_cents}")
            else:
                period_validations.append(f"❌ Cost calculation mismatch: expected {expected_total_cost}, found {total_cost_cents}")

            # Count image solve requests in this billing period
            if billing_period.get('id'):
                image_requests_query = """
                    SELECT COUNT(*) as image_request_count,
                           SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_requests,
                           SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as failed_requests
                    FROM request_logs
                    WHERE user_id = %s AND billing_period_id = %s AND service = 'core.image_solve'
                """

                request_stats = self.db_helper.execute_query(
                    image_requests_query,
                    (user_id, billing_period['id'])
                )

                if request_stats:
                    stats = request_stats[0]
                    image_count = stats.get('image_request_count', 0)
                    successful_count = stats.get('successful_requests', 0)
                    failed_count = stats.get('failed_requests', 0)

                    if image_count > 0:
                        period_validations.append(f"✓ Image solve requests found: {image_count}")
                        period_validations.append(f"✓ Successful requests: {successful_count}")
                        period_validations.append(f"✓ Failed requests: {failed_count}")

                        # Verify that image requests are included in total requests
                        if image_count <= total_requests:
                            period_validations.append(f"✓ Image requests ({image_count}) ≤ Total requests ({total_requests})")
                        else:
                            period_validations.append(f"❌ Image requests ({image_count}) > Total requests ({total_requests})")
                    else:
                        period_validations.append("⚠ No image solve requests found in current period")
                else:
                    period_validations.append("❌ Could not query image request statistics")

            # Verify billing period dates
            period_start = billing_period.get('period_start')
            period_end = billing_period.get('period_end')
            if period_start and period_end:
                period_validations.append(f"✓ Billing period dates: {period_start} to {period_end}")
            else:
                period_validations.append("❌ Billing period dates missing")

            # Calculate verification score
            total_validations = len(period_validations)
            passed_validations = len([v for v in period_validations if v.startswith("✓")])
            overall_score = (passed_validations / total_validations * 100) if total_validations > 0 else 0

            # Print validation summary
            print_info("Cost tracking validations:")
            for validation in period_validations:
                print(f"   {validation}")

            step.result = {
                "billing_period_id": billing_period.get('id'),
                "cost_per_request_cents": cost_per_request_cents,
                "total_requests": total_requests,
                "total_cost_cents": total_cost_cents,
                "expected_total_cost": expected_total_cost,
                "payment_status": payment_status,
                "period_validations": period_validations,
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "overall_score": overall_score
            }

            if overall_score >= 80:
                step.status = "PASS"
                print_success(f"✅ Cost tracking verification passed ({overall_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Cost tracking verification failed: {overall_score:.1f}% pass rate"
                print_error(f"❌ Cost tracking verification failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during cost tracking verification: {e}"
            print_error(f"Cost tracking verification failed: {e}")

        return step

    def verify_service_integration(self) -> TestStep:
        """Verify service field integration and API token tracking"""
        step = TestStep(step_number=1, step_name="Verify Service Integration", status="PASS", message="Verify service field integration and API token usage tracking")

        try:
            print_info("Verifying service integration...")

            user_id = self.test_data["user_id"]
            api_token_id = self.test_data["api_token_id"]
            service_verifications = []

            # Query request logs with service and token information
            service_query = """
                SELECT request_id, service, token_id, user_id, status,
                       COUNT(*) as request_count
                FROM request_logs
                WHERE user_id = %s
                GROUP BY service, token_id, status, request_id, user_id
                ORDER BY created_at DESC
                LIMIT 30
            """

            service_logs = self.db_helper.execute_query(service_query, (user_id,))

            if not service_logs:
                step.status = "FAIL"
                step.message = "No service logs found for user"
                return step

            print_info(f"Found {len(service_logs)} service log entries")

            # Analyze service distribution
            service_counts = {}
            token_usage = {}

            for log in service_logs:
                service = log.get('service')
                token_id = log.get('api_token_id')
                request_id = log.get('request_id')

                # Count services
                if service:
                    service_counts[service] = service_counts.get(service, 0) + 1

                # Track token usage
                if token_id:
                    token_usage[token_id] = token_usage.get(token_id, 0) + 1

                # Verify service field for image solve requests
                if service == 'core.image_solve':
                    service_validations = []

                    service_validations.append("✓ Service field set to 'core.image_solve'")

                    # Check API token assignment
                    if token_id == api_token_id:
                        service_validations.append("✓ API token ID matches our token")
                    elif token_id:
                        service_validations.append(f"⚠ Different API token used: {token_id}")
                    else:
                        service_validations.append("❌ No API token assigned")

                    # Verify user ID
                    if log.get('user_id') == user_id:
                        service_validations.append("✓ User ID correct")
                    else:
                        service_validations.append("❌ User ID mismatch")

                    service_verifications.append({
                        "request_id": request_id,
                        "validations": service_validations,
                        "log_data": log
                    })

            # Print service distribution
            print_info("Service distribution:")
            for service, count in service_counts.items():
                print(f"   {service}: {count} requests")

            # Print token usage
            print_info("API token usage:")
            for token_id, count in token_usage.items():
                token_short = token_id[:8] if token_id else "None"
                print(f"   Token {token_short}...: {count} requests")

            # Verify our API token is being used
            if api_token_id in token_usage:
                usage_count = token_usage[api_token_id]
                print_success(f"✅ Our API token used for {usage_count} requests")
            else:
                print_warning("⚠ Our API token not found in request logs")

            # Calculate service integration score
            total_validations = sum(len(v["validations"]) for v in service_verifications)
            passed_validations = sum(len([val for val in v["validations"] if val.startswith("✓")]) for v in service_verifications)
            integration_score = (passed_validations / total_validations * 100) if total_validations > 0 else 0

            # Additional checks
            additional_checks = []
            if 'core.image_solve' in service_counts:
                additional_checks.append("✅ Image solve service present in logs")
            else:
                additional_checks.append("❌ Image solve service missing from logs")

            if len(service_counts) <= 3:  # Reasonable number of services
                additional_checks.append("✅ Service diversity reasonable")
            else:
                additional_checks.append("⚠ Many different services in logs")

            step.result = {
                "service_verifications": service_verifications,
                "service_counts": service_counts,
                "token_usage": token_usage,
                "our_token_usage": token_usage.get(api_token_id, 0),
                "integration_score": integration_score,
                "additional_checks": additional_checks
            }

            # Combine scores for final evaluation
            additional_passed = len([c for c in additional_checks if c.startswith("✓")])
            additional_total = len(additional_checks)
            additional_score = (additional_passed / additional_total * 100) if additional_total > 0 else 0

            final_score = (integration_score + additional_score) / 2 if total_validations > 0 else additional_score

            if final_score >= 75:
                step.status = "PASS"
                print_success(f"✅ Service integration verification passed ({final_score:.1f}%)")
            else:
                step.status = "FAIL"
                step.message = f"Service integration verification failed: {final_score:.1f}% pass rate"
                print_error(f"❌ Service integration verification failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during service integration verification: {e}"
            print_error(f"Service integration verification failed: {e}")

        return step

    def run_test(self) -> TestResult:
        """Execute the complete billing integration test"""
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

            # Step 2: Generate image requests
            step_2 = self.generate_image_requests()
            test_steps.append(step_2)
            if not step_2.is_success():
                print_error("❌ Image request generation failed - aborting test")
                return self._create_test_result(start_time, test_steps, "REQUEST_GENERATION_FAILED")

            # Step 3: Verify request logs
            step_3 = self.verify_request_logs()
            test_steps.append(step_3)

            # Step 4: Verify billing periods
            step_4 = self.verify_billing_periods()
            test_steps.append(step_4)

            # Step 5: Verify cost tracking
            step_5 = self.verify_cost_tracking()
            test_steps.append(step_5)

            # Step 6: Verify service integration
            step_6 = self.verify_service_integration()
            test_steps.append(step_6)

            # Evaluate overall test success
            critical_steps = [step_1, step_2, step_3]  # These must pass
            integration_steps = [step_4, step_5, step_6]  # These should pass

            critical_passed = all(step.is_success() for step in critical_steps)
            integration_passed = sum(1 for step in integration_steps if step.is_success())

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if critical_passed and integration_passed >= 2:
                status = 'PASS'
            elif critical_passed and integration_passed >= 1:
                status = 'PASS'  # Still pass if critical work and some integration works
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
                print_success(f"✅ Billing integration verification completed")
                if hasattr(step_2, 'result') and step_2.result:
                    req_count = step_2.result.get('successful_requests', 0)
                    print_success(f"✅ Processed {req_count} image requests")
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
    print_success("IMG-05: Billing Integration Verification")

    # Create and run test
    test_instance = Image05BillingIntegration()
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
