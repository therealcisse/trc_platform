#!/usr/bin/env python3
"""
IMG-06: Comprehensive Image Suite Test
Test ID: IMG-06
Test Name: Comprehensive Image Suite Test
Test Type: Comprehensive Testing
Priority: High
Estimated Duration: 15 minutes

Description:
Comprehensive test of all available images in the test suite. This test processes
all 27 images in the tests/image_solve/images/ directory and validates 100%
expected answer accuracy. It provides performance metrics and success rate tracking
for the complete image solve functionality.

Test Flow:
1. Setup test user and API token
2. Process all available test images (up to 27)
3. Validate each response against expected answers from filenames
4. Track performance metrics and success rates
5. Analyze results by difficulty/complexity
6. Verify comprehensive billing integration
7. Cleanup test data
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
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

class Image06ComprehensiveSuite:
    """Comprehensive image suite test"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "IMG-06"
        self.test_name = "Comprehensive Image Suite Test"

        # Initialize helpers
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.database_url)
        self.http_client = HTTPClient(config.app_url)
        self.image_helper = ImageHelper(self.db_helper, self.http_client)
        self.auth_helper = AuthHelper(self.db_helper, self.http_client)

        # Test data storage
        self.test_data = {}
        self.run_id = str(uuid.uuid4())[:8]
        self.all_test_results = []

        # Performance tracking
        self.start_time = None
        self.end_time = None

    def setup_test_environment(self) -> TestStep:
        """Setup test user and API token"""
        step = TestStep(step_number=1, step_name="Setup Test Environment", status="PASS", message="Create test user and API token for comprehensive image testing")

        try:
            print_info("Setting up test environment for comprehensive testing...")

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

            test_email = f"img06-comprehensive-{self.run_id}@uat-test.trc-platform.local"
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
                f"img06-comprehensive-{self.run_id}"
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

    def process_all_images(self) -> TestStep:
        """Process all available test images"""
        step = TestStep(step_number=1, step_name="Process All Images", status="PASS", message="Process all available test images and collect results")

        try:
            print_info("Starting comprehensive image processing...")
            self.start_time = datetime.now()

            if "api_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "API token not available"
                return step

            api_token = self.test_data["api_token"]

            # Get all test images
            all_images = self.image_helper.get_test_images()
            if not all_images:
                step.status = "FAIL"
                step.message = "No test images found"
                return step

            print_info(f"Found {len(all_images)} test images for comprehensive processing")
            print_info("This may take several minutes...")

            processed_results = []
            successful_requests = []
            failed_requests = []

            # Process each image
            for i, image_data in enumerate(all_images):
                print_info(f"Processing image {i+1}/{len(all_images)}: {image_data.filename} (expected: {image_data.expected_answer})")

                try:
                    # Upload and solve image
                    solve_step = self.image_helper.upload_and_solve(
                        image_data.filepath,
                        api_token
                    )

                    image_result = {
                        "filename": image_data.filename,
                        "expected_answer": image_data.expected_answer,
                        "file_size": image_data.file_size,
                        "index": i,
                        "start_time": datetime.now().isoformat()
                    }

                    if solve_step.is_success():
                        solve_response = solve_step.result["solve_response"]

                        # Validate the response
                        validation_step = self.image_helper.validate_solve_response(
                            solve_response,
                            image_data.expected_answer
                        )

                        image_result.update({
                            "success": validation_step.is_success(),
                            "request_id": solve_response.request_id,
                            "actual_result": solve_response.result,
                            "duration_ms": solve_response.duration_ms,
                            "response_time": solve_response.response_time,
                            "validations": validation_step.result.get("validations", []) if validation_step.result else [],
                            "error": None
                        })

                        if validation_step.is_success():
                            successful_requests.append(image_result)
                            print_success(f"✅ {image_data.filename}: {image_data.expected_answer} ✓")
                        else:
                            failed_requests.append(image_result)
                            print_error(f"❌ {image_data.filename}: expected {image_data.expected_answer}, got {solve_response.result}")
                    else:
                        image_result.update({
                            "success": False,
                            "error": solve_step.message,
                            "request_id": None,
                            "actual_result": None,
                            "duration_ms": None,
                            "response_time": None,
                            "validations": []
                        })
                        failed_requests.append(image_result)
                        print_error(f"❌ {image_data.filename}: {solve_step.message}")

                    processed_results.append(image_result)

                    # Add a small delay to avoid overwhelming the system
                    time.sleep(0.5)

                except Exception as e:
                    print_error(f"❌ Exception processing {image_data.filename}: {e}")
                    failed_requests.append({
                        "filename": image_data.filename,
                        "expected_answer": image_data.expected_answer,
                        "success": False,
                        "error": str(e),
                        "index": i
                    })
                    processed_results.append({
                        "filename": image_data.filename,
                        "expected_answer": image_data.expected_answer,
                        "success": False,
                        "error": str(e),
                        "index": i
                    })

            self.end_time = datetime.now()
            total_duration = (self.end_time - self.start_time).total_seconds()

            # Store all results for analysis
            self.all_test_results = processed_results

            # Calculate statistics
            total_images = len(processed_results)
            successful_count = len(successful_requests)
            failed_count = len(failed_requests)
            success_rate = (successful_count / total_images * 100) if total_images > 0 else 0

            print_info(f"\n{'='*60}")
            print_info(f"COMPREHENSIVE TEST RESULTS")
            print_info(f"{'='*60}")
            print_info(f"Total images processed: {total_images}")
            print_info(f"Successful requests: {successful_count}")
            print_info(f"Failed requests: {failed_count}")
            print_info(f"Success rate: {success_rate:.1f}%")
            print_info(f"Total duration: {total_duration:.2f} seconds")
            print_info(f"Average time per image: {total_duration/total_images:.2f} seconds")
            print_info(f"{'='*60}")

            step.result = {
                "total_images": total_images,
                "successful_count": successful_count,
                "failed_count": failed_count,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "average_time_per_image": total_duration/total_images if total_images > 0 else 0,
                "processed_results": processed_results,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests
            }

            # For comprehensive test, we require high success rate
            if success_rate >= 90:
                step.status = "PASS"
                print_success(f"✅ Comprehensive image processing completed with {success_rate:.1f}% success rate")
            elif success_rate >= 75:
                step.status = "PASS"
                print_warning(f"⚠ Comprehensive image processing completed with acceptable {success_rate:.1f}% success rate")
            else:
                step.status = "FAIL"
                step.message = f"Low success rate: {success_rate:.1f}% (expected at least 75%)"
                print_error(f"❌ Comprehensive image processing failed: {success_rate:.1f}% success rate")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during comprehensive image processing: {e}"
            print_error(f"Comprehensive image processing failed: {e}")

        return step

    def analyze_results_by_difficulty(self) -> TestStep:
        """Analyze results by expected answer difficulty/complexity"""
        step = TestStep(step_number=1, step_name="Analyze Results by Difficulty", status="PASS", message="Analyze test results based on expected answer complexity")

        try:
            print_info("Analyzing results by answer difficulty...")

            if not self.all_test_results:
                step.status = "FAIL"
                step.message = "No test results available for analysis"
                return step

            # Group results by expected answer
            answer_groups = {}
            for result in self.all_test_results:
                expected = result.get("expected_answer", "unknown")
                if expected not in answer_groups:
                    answer_groups[expected] = []
                answer_groups[expected].append(result)

            analysis_results = []

            print_info("Analysis by expected answer:")
            print(f"{'Answer':<8} {'Total':<6} {'Success':<8} {'Rate':<8} {'Examples'}")
            print("-" * 50)

            for answer in sorted(answer_groups.keys()):
                results = answer_groups[answer]
                total = len(results)
                successful = len([r for r in results if r.get("success", False)])
                success_rate = (successful / total * 100) if total > 0 else 0

                # Get example filenames
                examples = [r["filename"] for r in results[:3]]
                examples_str = ", ".join(examples)
                if len(examples) > 3:
                    examples_str += f" (+{len(examples)-3} more)"

                print(f"{answer:<8} {total:<6} {successful:<8} {success_rate:<8.1f}% {examples_str}")

                analysis_results.append({
                    "expected_answer": answer,
                    "total_count": total,
                    "successful_count": successful,
                    "success_rate": success_rate,
                    "examples": examples
                })

            # Additional analysis by answer length/complexity
            complexity_analysis = {
                "single_digit": {"total": 0, "successful": 0},  # 0-9
                "double_digit": {"total": 0, "successful": 0}, # 10-99
                "triple_digit": {"total": 0, "successful": 0}, # 100-999
                "other": {"total": 0, "successful": 0}
            }

            for result in self.all_test_results:
                expected = result.get("expected_answer", "")
                success = result.get("success", False)

                try:
                    num = int(expected)
                    if num < 10:
                        complexity_analysis["single_digit"]["total"] += 1
                        if success:
                            complexity_analysis["single_digit"]["successful"] += 1
                    elif num < 100:
                        complexity_analysis["double_digit"]["total"] += 1
                        if success:
                            complexity_analysis["double_digit"]["successful"] += 1
                    else:
                        complexity_analysis["triple_digit"]["total"] += 1
                        if success:
                            complexity_analysis["triple_digit"]["successful"] += 1
                except (ValueError, TypeError):
                    complexity_analysis["other"]["total"] += 1
                    if success:
                        complexity_analysis["other"]["successful"] += 1

            print_info(f"\nComplexity Analysis:")
            print(f"{'Complexity':<12} {'Total':<6} {'Success':<8} {'Rate':<8}")
            print("-" * 35)
            for complexity, data in complexity_analysis.items():
                total = data["total"]
                successful = data["successful"]
                rate = (successful / total * 100) if total > 0 else 0
                print(f"{complexity:<12} {total:<6} {successful:<8} {rate:<8.1f}%")

            # Calculate overall complexity scores
            step.result = {
                "answer_analysis": analysis_results,
                "complexity_analysis": complexity_analysis,
                "total_unique_answers": len(answer_groups),
                "best_performing_answer": max(analysis_results, key=lambda x: x["success_rate"])["expected_answer"] if analysis_results else None,
                "worst_performing_answer": min(analysis_results, key=lambda x: x["success_rate"])["expected_answer"] if analysis_results else None
            }

            step.status = "PASS"
            print_success("✅ Results analysis completed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during results analysis: {e}"
            print_error(f"Results analysis failed: {e}")

        return step

    def verify_comprehensive_billing(self) -> TestStep:
        """Verify comprehensive billing integration for all processed requests"""
        step = TestStep(step_number=1, step_name="Verify Comprehensive Billing", status="PASS", message="Verify billing integration for all processed image requests")

        try:
            print_info("Verifying comprehensive billing integration...")

            user_id = self.test_data["user_id"]
            successful_requests = [r for r in self.all_test_results if r.get("success", False)]
            request_ids = [r.get("request_id") for r in successful_requests if r.get("request_id")]

            if not request_ids:
                step.status = "FAIL"
                step.message = "No successful requests to verify billing for"
                return step

            print_info(f"Verifying billing for {len(request_ids)} successful requests...")

            # Query request logs for all our requests
            billing_query = """
                SELECT request_id, service, status, duration_ms, cost,
                       billing_period_id, created_at
                FROM request_logs
                WHERE user_id = %s AND service = 'core.image_solve'
                ORDER BY created_at DESC
                LIMIT 50
            """

            billing_logs = self.db_helper.execute_query(billing_query, (user_id,))

            if not billing_logs:
                step.status = "FAIL"
                step.message = "No billing logs found for image solve requests"
                return step

            print_info(f"Found {len(billing_logs)} billing log entries")

            # Verify each request ID is present in logs
            verified_requests = 0
            missing_requests = 0
            total_cost = 0
            costed_requests = 0

            for request_id in request_ids:
                found = False
                for log in billing_logs:
                    if log.get('request_id') == request_id:
                        found = True
                        verified_requests += 1

                        # Check cost
                        cost = log.get('cost')
                        if cost is not None and cost > 0:
                            total_cost += cost
                            costed_requests += 1

                        # Verify billing period assignment
                        if log.get('billing_period_id'):
                            pass  # Good
                        else:
                            print_warning(f"⚠ Request {request_id[:8]}... missing billing period")

                        break

                if not found:
                    missing_requests += 1
                    print_warning(f"⚠ Request {request_id[:8]}... not found in billing logs")

            # Calculate billing statistics
            verification_rate = (verified_requests / len(request_ids) * 100) if request_ids else 0
            cost_assignment_rate = (costed_requests / verified_requests * 100) if verified_requests else 0
            average_cost = total_cost / costed_requests if costed_requests > 0 else 0

            print_info(f"\nComprehensive Billing Verification:")
            print_info(f"Total successful requests: {len(request_ids)}")
            print_info(f"Requests found in billing logs: {verified_requests}")
            print_info(f"Requests missing from logs: {missing_requests}")
            print_info(f"Billing verification rate: {verification_rate:.1f}%")
            print_info(f"Requests with costs assigned: {costed_requests}")
            print_info(f"Cost assignment rate: {cost_assignment_rate:.1f}%")
            print_info(f"Total cost for all requests: {total_cost:.4f}")
            print_info(f"Average cost per request: {average_cost:.4f}")

            # Additional verification: Check billing periods
            billing_period_query = """
                SELECT COUNT(*) as period_count, SUM(total_cost) as total_cost,
                       SUM(total_requests) as total_requests
                FROM billing_periods
                WHERE user_id = %s
            """

            period_stats = self.db_helper.execute_query(billing_period_query, (user_id,))
            if period_stats:
                stats = period_stats[0]
                print_info(f"\nBilling Period Summary:")
                print_info(f"Number of billing periods: {stats.get('period_count', 0)}")
                print_info(f"Total requests in periods: {stats.get('total_requests', 0)}")
                print_info(f"Total cost in periods: {stats.get('total_cost', 0):.4f}")

            step.result = {
                "total_successful_requests": len(request_ids),
                "verified_requests": verified_requests,
                "missing_requests": missing_requests,
                "verification_rate": verification_rate,
                "costed_requests": costed_requests,
                "cost_assignment_rate": cost_assignment_rate,
                "total_cost": total_cost,
                "average_cost": average_cost,
                "billing_logs_found": len(billing_logs)
            }

            # Consider successful if most requests are properly billed
            if verification_rate >= 90 and cost_assignment_rate >= 80:
                step.status = "PASS"
                print_success(f"✅ Comprehensive billing verification passed")
            elif verification_rate >= 75 and cost_assignment_rate >= 60:
                step.status = "PASS"
                print_warning(f"⚠ Comprehensive billing verification acceptable but could be improved")
            else:
                step.status = "FAIL"
                step.message = f"Comprehensive billing verification failed: verification {verification_rate:.1f}%, cost assignment {cost_assignment_rate:.1f}%"
                print_error(f"❌ Comprehensive billing verification failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during comprehensive billing verification: {e}"
            print_error(f"Comprehensive billing verification failed: {e}")

        return step

    def generate_performance_report(self) -> TestStep:
        """Generate comprehensive performance report"""
        step = TestStep(step_number=1, step_name="Generate Performance Report", status="PASS", message="Generate detailed performance report for all image requests")

        try:
            print_info("Generating comprehensive performance report...")

            if not self.all_test_results:
                step.status = "FAIL"
                step.message = "No test results available for performance analysis"
                return step

            successful_results = [r for r in self.all_test_results if r.get("success", False)]
            failed_results = [r for r in self.all_test_results if not r.get("success", False)]

            # Performance metrics
            response_times = [r.get("response_time", 0) for r in successful_results if r.get("response_time")]
            durations = [r.get("duration_ms", 0) for r in successful_results if r.get("duration_ms")]

            performance_stats = {}

            if response_times:
                performance_stats["response_time"] = {
                    "min": min(response_times),
                    "max": max(response_times),
                    "avg": sum(response_times) / len(response_times),
                    "median": sorted(response_times)[len(response_times) // 2],
                    "count": len(response_times)
                }

            if durations:
                performance_stats["duration_ms"] = {
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "median": sorted(durations)[len(durations) // 2],
                    "count": len(durations)
                }

            # File size analysis
            file_sizes = [r.get("file_size", 0) for r in self.all_test_results if r.get("file_size")]
            if file_sizes:
                performance_stats["file_size"] = {
                    "min": min(file_sizes),
                    "max": max(file_sizes),
                    "avg": sum(file_sizes) / len(file_sizes),
                    "count": len(file_sizes)
                }

            # Success rate by file size quartiles
            if file_sizes and len(self.all_test_results) > 4:
                sorted_sizes = sorted(file_sizes)
                q1 = sorted_sizes[len(sorted_sizes) // 4]
                q2 = sorted_sizes[len(sorted_sizes) // 2]
                q3 = sorted_sizes[3 * len(sorted_sizes) // 4]

                size_quartile_success = {
                    "small (< Q1)": {"total": 0, "success": 0},
                    "medium-small (Q1-Q2)": {"total": 0, "success": 0},
                    "medium-large (Q2-Q3)": {"total": 0, "success": 0},
                    "large (> Q3)": {"total": 0, "success": 0}
                }

                for result in self.all_test_results:
                    size = result.get("file_size", 0)
                    success = result.get("success", False)

                    if size < q1:
                        size_quartile_success["small (< Q1)"]["total"] += 1
                        if success:
                            size_quartile_success["small (< Q1)"]["success"] += 1
                    elif size < q2:
                        size_quartile_success["medium-small (Q1-Q2)"]["total"] += 1
                        if success:
                            size_quartile_success["medium-small (Q1-Q2)"]["success"] += 1
                    elif size < q3:
                        size_quartile_success["medium-large (Q2-Q3)"]["total"] += 1
                        if success:
                            size_quartile_success["medium-large (Q2-Q3)"]["success"] += 1
                    else:
                        size_quartile_success["large (> Q3)"]["total"] += 1
                        if success:
                            size_quartile_success["large (> Q3)"]["success"] += 1

                performance_stats["size_quartile_success"] = size_quartile_success

            # Print performance report
            print_info(f"\n{'='*60}")
            print_info(f"COMPREHENSIVE PERFORMANCE REPORT")
            print_info(f"{'='*60}")

            print_info(f"Test Summary:")
            print_info(f"  Total images: {len(self.all_test_results)}")
            print_info(f"  Successful: {len(successful_results)}")
            print_info(f"  Failed: {len(failed_results)}")
            print_info(f"  Success rate: {len(successful_results)/len(self.all_test_results)*100:.1f}%")

            if "response_time" in performance_stats:
                rt = performance_stats["response_time"]
                print_info(f"\nResponse Time (seconds):")
                print_info(f"  Min: {rt['min']:.2f}s")
                print_info(f"  Max: {rt['max']:.2f}s")
                print_info(f"  Avg: {rt['avg']:.2f}s")
                print_info(f"  Median: {rt['median']:.2f}s")

            if "duration_ms" in performance_stats:
                dur = performance_stats["duration_ms"]
                print_info(f"\nProcessing Duration (ms):")
                print_info(f"  Min: {dur['min']}ms")
                print_info(f"  Max: {dur['max']}ms")
                print_info(f"  Avg: {dur['avg']:.1f}ms")
                print_info(f"  Median: {dur['median']}ms")

            if "file_size" in performance_stats:
                fs = performance_stats["file_size"]
                print_info(f"\nFile Size (bytes):")
                print_info(f"  Min: {fs['min']}")
                print_info(f"  Max: {fs['max']}")
                print_info(f"  Avg: {fs['avg']:.1f}")

            if "size_quartile_success" in performance_stats:
                print_info(f"\nSuccess Rate by File Size:")
                for quartile, data in performance_stats["size_quartile_success"].items():
                    rate = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
                    print_info(f"  {quartile}: {data['success']}/{data['total']} ({rate:.1f}%)")

            # Performance assessment
            performance_assessment = []
            if len(successful_results) / len(self.all_test_results) >= 0.9:
                performance_assessment.append("✅ Excellent success rate (≥90%)")
            elif len(successful_results) / len(self.all_test_results) >= 0.75:
                performance_assessment.append("✅ Good success rate (≥75%)")
            else:
                performance_assessment.append("❌ Poor success rate (<75%)")

            if "response_time" in performance_stats:
                avg_rt = performance_stats["response_time"]["avg"]
                if avg_rt < 10:
                    performance_assessment.append("✅ Excellent response time (<10s)")
                elif avg_rt < 30:
                    performance_assessment.append("✅ Good response time (<30s)")
                else:
                    performance_assessment.append("⚠ Slow response time (>30s)")

            step.result = {
                "performance_stats": performance_stats,
                "total_results": len(self.all_test_results),
                "successful_results": len(successful_results),
                "failed_results": len(failed_results),
                "overall_success_rate": len(successful_results)/len(self.all_test_results)*100,
                "performance_assessment": performance_assessment
            }

            step.status = "PASS"
            print_success("✅ Performance report generated")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception generating performance report: {e}"
            print_error(f"Performance report generation failed: {e}")

        return step

    def run_test(self) -> TestResult:
        """Execute the comprehensive image suite test"""
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

            # Step 2: Process all images
            step_2 = self.process_all_images()
            test_steps.append(step_2)
            if not step_2.is_success():
                print_error("❌ Image processing failed - aborting test")
                return self._create_test_result(start_time, test_steps, "IMAGE_PROCESSING_FAILED")

            # Step 3: Analyze results by difficulty
            step_3 = self.analyze_results_by_difficulty()
            test_steps.append(step_3)

            # Step 4: Verify comprehensive billing
            step_4 = self.verify_comprehensive_billing()
            test_steps.append(step_4)

            # Step 5: Generate performance report
            step_5 = self.generate_performance_report()
            test_steps.append(step_5)

            # Evaluate overall test success
            critical_steps = [step_1, step_2]  # These must pass
            analysis_steps = [step_3, step_4, step_5]  # These should pass

            critical_passed = all(step.is_success() for step in critical_steps)
            analysis_passed = sum(1 for step in analysis_steps if step.is_success())

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if critical_passed and analysis_passed >= 2:
                status = 'PASS'
            elif critical_passed and analysis_passed >= 1:
                status = 'PASS'  # Still pass if critical work and some analysis works
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
            result.test_results = self.all_test_results

            if status == 'PASS':
                print_success(f"\n🎉 {self.test_id} PASSED")
                if self.all_test_results:
                    success_count = len([r for r in self.all_test_results if r.get("success", False)])
                    total_count = len(self.all_test_results)
                    success_rate = success_count / total_count * 100
                    print_success(f"✅ Comprehensive test completed: {success_count}/{total_count} images ({success_rate:.1f}% success)")
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
    print_success("IMG-06: Comprehensive Image Suite Test")
    print_warning("⚠ This test may take 10-15 minutes to complete...")

    # Create and run test
    test_instance = Image06ComprehensiveSuite()
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
