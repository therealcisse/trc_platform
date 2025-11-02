package test

import (
	"context"
	"fmt"
	"time"

	"uat/framework"
	"uat/helpers"
)

// TestDomain implements the framework.Domain interface for testing
type TestDomain struct {
	name        string
	description string
	tests       []framework.Test
}

// NewTestDomain creates a new test domain
func NewTestDomain() *TestDomain {
	domain := &TestDomain{
		name:        "test",
		description: "Test domain for framework validation and simple use cases",
		tests:       make([]framework.Test, 0),
	}

	// Add default tests
	domain.addDefaultTests()

	return domain
}

// Name returns the domain name
func (td *TestDomain) Name() string {
	return td.name
}

// Description returns the domain description
func (td *TestDomain) Description() string {
	return td.description
}

// Setup sets up the test domain
func (td *TestDomain) Setup(ctx context.Context, fw *framework.Framework) error {
	// Test framework connectivity
	if err := fw.Database.Ping(ctx); err != nil {
		return fmt.Errorf("database connectivity test failed: %w", err)
	}

	// Test email connectivity
	if err := fw.Email.ConnectMailcatcher(ctx); err != nil {
		return fmt.Errorf("email connectivity test failed: %w", err)
	}

	return nil
}

// Cleanup cleans up the test domain
func (td *TestDomain) Cleanup(ctx context.Context, fw *framework.Framework) error {
	// No cleanup needed for test domain
	return nil
}

// GetTests returns all tests in this domain
func (td *TestDomain) GetTests() []framework.Test {
	return td.tests
}

// AddTest adds a test to the domain
func (td *TestDomain) AddTest(test framework.Test) {
	td.tests = append(td.tests, test)
}

// addDefaultTests adds default tests to the domain
func (td *TestDomain) addDefaultTests() {
	td.AddTest(&SimpleConnectivityTest{})
	td.AddTest(&BasicValidationTest{})
	td.AddTest(&ErrorHandlingTest{})
}

// Ping tests database connectivity
func (td *TestDomain) Ping(ctx context.Context, fw *framework.Framework) error {
	return fw.Database.Ping(ctx)
}

// SimpleConnectivityTest tests basic connectivity
type SimpleConnectivityTest struct{}

// ID returns the test ID
func (sct *SimpleConnectivityTest) ID() string {
	return "TEST-01"
}

// Name returns the test name
func (sct *SimpleConnectivityTest) Name() string {
	return "Framework Connectivity Test"
}

// Description returns the test description
func (sct *SimpleConnectivityTest) Description() string {
	return "Tests basic connectivity to all required services (database, email, application)"
}

// Priority returns the test priority
func (sct *SimpleConnectivityTest) Priority() int {
	return 1
}

// Required returns whether the test is required
func (sct *SimpleConnectivityTest) Required() bool {
	return true
}

// Execute executes the test
func (sct *SimpleConnectivityTest) Execute(ctx context.Context, fw *framework.Framework) framework.TestResult {
	startTime := time.Now()
	result := framework.TestResult{
		ID:         sct.ID(),
		Name:       sct.Name(),
		Status:     framework.TestStatusRunning,
		StartTime:  startTime,
		TestSteps:  make([]framework.TestStep, 0),
		TotalSteps: 3,
	}

	// Step 1: Test database connectivity
	step1 := framework.TestStep{
		Number: 1,
		Name:   "Database Connectivity Test",
		Status: framework.TestStatusRunning,
	}

	if err := fw.Database.Ping(ctx); err != nil {
		step1.Status = framework.TestStatusFail
		step1.Message = fmt.Sprintf("Database connectivity failed: %v", err)
		result.TestSteps = append(result.TestSteps, step1)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step1.Status = framework.TestStatusPass
	step1.Message = "Database connectivity successful"
	result.TestSteps = append(result.TestSteps, step1)
	result.PassedSteps = 1

	// Step 2: Test email connectivity
	step2 := framework.TestStep{
		Number: 2,
		Name:   "Email Connectivity Test",
		Status: framework.TestStatusRunning,
	}

	if err := fw.Email.ConnectMailcatcher(ctx); err != nil {
		step2.Status = framework.TestStatusFail
		step2.Message = fmt.Sprintf("Email connectivity failed: %v", err)
		result.TestSteps = append(result.TestSteps, step2)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step2.Status = framework.TestStatusPass
	step2.Message = "Email connectivity successful"
	result.TestSteps = append(result.TestSteps, step2)
	result.PassedSteps = 2

	// Step 3: Test application health endpoint
	step3 := framework.TestStep{
		Number: 3,
		Name:   "Application Health Check",
		Status: framework.TestStatusRunning,
	}

	// Simple hardcoded health endpoint for now
	endpoint, _ := fw.Config.GetEndpoint("health")

	resp, err := fw.HTTPClient.Get(ctx, endpoint, nil)
	if err != nil {
		step3.Status = framework.TestStatusFail
		step3.Message = fmt.Sprintf("Health check failed: %v", err)
		result.TestSteps = append(result.TestSteps, step3)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	if resp.Status != 200 {
		step3.Status = framework.TestStatusFail
		step3.Message = fmt.Sprintf("Health check returned status %d", resp.Status)
		result.TestSteps = append(result.TestSteps, step3)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step3.Status = framework.TestStatusPass
	step3.Message = "Application health check successful"
	step3.ResponseTime = resp.ResponseTime
	result.TestSteps = append(result.TestSteps, step3)
	result.PassedSteps = 3

	// Test completed successfully
	result.Status = framework.TestStatusPass
	endTime := time.Now()
	result.EndTime = &endTime
	result.TotalTime = endTime.Sub(startTime).Seconds()

	return result
}

// BasicValidationTest tests input validation functionality
type BasicValidationTest struct{}

// ID returns the test ID
func (bvt *BasicValidationTest) ID() string {
	return "TEST-02"
}

// Name returns the test name
func (bvt *BasicValidationTest) Name() string {
	return "Input Validation Test"
}

// Description returns the test description
func (bvt *BasicValidationTest) Description() string {
	return "Tests input validation functions for email, password, and invite codes"
}

// Priority returns the test priority
func (bvt *BasicValidationTest) Priority() int {
	return 2
}

// Required returns whether the test is required
func (bvt *BasicValidationTest) Required() bool {
	return true
}

// Execute executes the test
func (bvt *BasicValidationTest) Execute(ctx context.Context, fw *framework.Framework) framework.TestResult {
	startTime := time.Now()
	result := framework.TestResult{
		ID:         bvt.ID(),
		Name:       bvt.Name(),
		Status:     framework.TestStatusRunning,
		StartTime:  startTime,
		TestSteps:  make([]framework.TestStep, 0),
		TotalSteps: 3,
	}

	// Import validation helper
	validator := helpers.GlobalValidator

	// Step 1: Test email validation
	step1 := framework.TestStep{
		Number: 1,
		Name:   "Email Validation Test",
		Status: framework.TestStatusRunning,
	}

	// Test valid email
	validEmail := validator.ValidateEmail("test@example.com")
	if !validEmail.IsValid {
		step1.Status = framework.TestStatusFail
		step1.Message = "Valid email validation failed"
		result.TestSteps = append(result.TestSteps, step1)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	// Test invalid email
	invalidEmail := validator.ValidateEmail("invalid-email")
	if invalidEmail.IsValid {
		step1.Status = framework.TestStatusFail
		step1.Message = "Invalid email validation should have failed"
		result.TestSteps = append(result.TestSteps, step1)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step1.Status = framework.TestStatusPass
	step1.Message = "Email validation tests passed"
	result.TestSteps = append(result.TestSteps, step1)
	result.PassedSteps = 1

	// Step 2: Test password validation
	step2 := framework.TestStep{
		Number: 2,
		Name:   "Password Validation Test",
		Status: framework.TestStatusRunning,
	}

	// Test valid password
	validPassword := validator.ValidatePassword("TestPass123!", "Password")
	if !validPassword.IsValid {
		step2.Status = framework.TestStatusFail
		step2.Message = "Valid password validation failed"
		result.TestSteps = append(result.TestSteps, step2)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	// Test weak password
	weakPassword := validator.ValidatePassword("weak", "Password")
	if weakPassword.IsValid {
		step2.Status = framework.TestStatusFail
		step2.Message = "Weak password validation should have failed"
		result.TestSteps = append(result.TestSteps, step2)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step2.Status = framework.TestStatusPass
	step2.Message = "Password validation tests passed"
	result.TestSteps = append(result.TestSteps, step2)
	result.PassedSteps = 2

	// Step 3: Test invite code validation
	step3 := framework.TestStep{
		Number: 3,
		Name:   "Invite Code Validation Test",
		Status: framework.TestStatusRunning,
	}

	// Test valid invite code
	validCode := validator.ValidateInviteCode("TEST-CODE-123")
	if !validCode.IsValid {
		step3.Status = framework.TestStatusFail
		step3.Message = "Valid invite code validation failed"
		result.TestSteps = append(result.TestSteps, step3)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	// Test invalid invite code (too short)
	invalidCode := validator.ValidateInviteCode("short")
	if invalidCode.IsValid {
		step3.Status = framework.TestStatusFail
		step3.Message = "Short invite code validation should have failed"
		result.TestSteps = append(result.TestSteps, step3)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step3.Status = framework.TestStatusPass
	step3.Message = "Invite code validation tests passed"
	result.TestSteps = append(result.TestSteps, step3)
	result.PassedSteps = 3

	// Test completed successfully
	result.Status = framework.TestStatusPass
	endTime := time.Now()
	result.EndTime = &endTime
	result.TotalTime = endTime.Sub(startTime).Seconds()

	return result
}

// ErrorHandlingTest tests error handling functionality
type ErrorHandlingTest struct{}

// ID returns the test ID
func (eht *ErrorHandlingTest) ID() string {
	return "TEST-03"
}

// Name returns the test name
func (eht *ErrorHandlingTest) Name() string {
	return "Error Handling Test"
}

// Description returns the test description
func (eht *ErrorHandlingTest) Description() string {
	return "Tests error handling and logging functionality"
}

// Priority returns the test priority
func (eht *ErrorHandlingTest) Priority() int {
	return 3
}

// Required returns whether the test is required
func (eht *ErrorHandlingTest) Required() bool {
	return true
}

// Execute executes the test
func (eht *ErrorHandlingTest) Execute(ctx context.Context, fw *framework.Framework) framework.TestResult {
	startTime := time.Now()
	result := framework.TestResult{
		ID:         eht.ID(),
		Name:       eht.Name(),
		Status:     framework.TestStatusRunning,
		StartTime:  startTime,
		TestSteps:  make([]framework.TestStep, 0),
		TotalSteps: 2,
	}

	// Step 1: Test error creation and handling
	step1 := framework.TestStep{
		Number: 1,
		Name:   "Error Creation Test",
		Status: framework.TestStatusRunning,
	}

	// Create a test error
	context := helpers.CreateErrorContext("test_operation", "test_component", map[string]interface{}{
		"test_data": "sample_value",
	})

	testError := fmt.Errorf("test error for validation")
	uatError := helpers.GlobalErrorHandler.HandleError(testError, helpers.ErrorCategoryTest, helpers.ErrorSeverityLow, context)

	if uatError == nil {
		step1.Status = framework.TestStatusFail
		step1.Message = "Error creation failed"
		result.TestSteps = append(result.TestSteps, step1)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	if uatError.Category != helpers.ErrorCategoryTest {
		step1.Status = framework.TestStatusFail
		step1.Message = fmt.Sprintf("Expected error category Test, got %s", uatError.Category)
		result.TestSteps = append(result.TestSteps, step1)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step1.Status = framework.TestStatusPass
	step1.Message = "Error creation test passed"
	result.TestSteps = append(result.TestSteps, step1)
	result.PassedSteps = 1

	// Step 2: Test error summary
	step2 := framework.TestStep{
		Number: 2,
		Name:   "Error Summary Test",
		Status: framework.TestStatusRunning,
	}

	summary := helpers.GlobalErrorHandler.GetErrorSummary()
	if summary == nil {
		step2.Status = framework.TestStatusFail
		step2.Message = "Error summary generation failed"
		result.TestSteps = append(result.TestSteps, step2)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	totalErrors, ok := summary["total_errors"].(int)
	if !ok || totalErrors < 1 {
		step2.Status = framework.TestStatusFail
		step2.Message = "Expected at least 1 error in summary"
		result.TestSteps = append(result.TestSteps, step2)
		result.Status = framework.TestStatusFail
		result.FailedSteps = 1
		result.EndTime = &[]time.Time{time.Now()}[0]
		result.TotalTime = time.Since(startTime).Seconds()
		return result
	}

	step2.Status = framework.TestStatusPass
	step2.Message = fmt.Sprintf("Error summary test passed - %d errors logged", totalErrors)
	result.TestSteps = append(result.TestSteps, step2)
	result.PassedSteps = 2

	// Test completed successfully
	result.Status = framework.TestStatusPass
	endTime := time.Now()
	result.EndTime = &endTime
	result.TotalTime = endTime.Sub(startTime).Seconds()

	return result
}
