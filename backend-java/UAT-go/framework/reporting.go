package framework

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

// TestReporting handles test result collection and reporting
type TestReporting struct {
	mu          sync.RWMutex
	startTime   time.Time
	endTime     *time.Time
	testResults []TestResult
	verbose     bool
}

// NewTestReporting creates a new test reporting instance
func NewTestReporting() *TestReporting {
	return &TestReporting{
		startTime:   time.Now(),
		testResults: make([]TestResult, 0),
		verbose:     false,
	}
}

// SetVerbose sets verbose reporting mode
func (tr *TestReporting) SetVerbose(verbose bool) {
	tr.mu.Lock()
	defer tr.mu.Unlock()
	tr.verbose = verbose
}

// AddTestResult adds a test result to the collection
func (tr *TestReporting) AddTestResult(result TestResult) {
	tr.mu.Lock()
	defer tr.mu.Unlock()
	tr.testResults = append(tr.testResults, result)
}

// GetTestResults returns a copy of all test results
func (tr *TestReporting) GetTestResults() []TestResult {
	tr.mu.RLock()
	defer tr.mu.RUnlock()

	results := make([]TestResult, len(tr.testResults))
	copy(results, tr.testResults)
	return results
}

// SetEndTime marks the completion time of the test suite
func (tr *TestReporting) SetEndTime() {
	tr.mu.Lock()
	defer tr.mu.Unlock()
	now := time.Now()
	tr.endTime = &now
}

// GetDuration returns the total duration of the test suite
func (tr *TestReporting) GetDuration() time.Duration {
	tr.mu.RLock()
	defer tr.mu.RUnlock()

	end := tr.endTime
	if end == nil {
		end = &[]time.Time{time.Now()}[0]
	}
	return end.Sub(tr.startTime)
}

// GetSummary returns a summary of test results
func (tr *TestReporting) GetSummary() TestSummary {
	tr.mu.RLock()
	defer tr.mu.RUnlock()

	totalTests := len(tr.testResults)
	passedTests := 0
	failedTests := 0
	errorTests := 0
	skippedTests := 0
	totalSteps := 0
	passedSteps := 0
	failedSteps := 0
	errorSteps := 0
	skippedSteps := 0

	for _, result := range tr.testResults {
		switch result.Status {
		case TestStatusPass:
			passedTests++
		case TestStatusFail:
			failedTests++
		case TestStatusError:
			errorTests++
		case TestStatusSkip:
			skippedTests++
		}

		totalSteps += result.TotalSteps
		passedSteps += result.PassedSteps
		failedSteps += result.FailedSteps
		errorSteps += result.ErrorSteps
		skippedSteps += result.SkippedSteps
	}

	return TestSummary{
		TotalTests:     totalTests,
		PassedTests:    passedTests,
		FailedTests:    failedTests,
		ErrorTests:     errorTests,
		SkippedTests:   skippedTests,
		TotalSteps:     totalSteps,
		PassedSteps:    passedSteps,
		FailedSteps:    failedSteps,
		ErrorSteps:     errorSteps,
		SkippedSteps:   skippedSteps,
		Duration:       tr.GetDuration().Seconds(),
		StartTime:      tr.startTime,
		EndTime:        tr.endTime,
		TestSuccessRate: float64(passedTests) / float64(totalTests) * 100,
		StepSuccessRate: float64(passedSteps) / float64(totalSteps) * 100,
	}
}

// PrintTestHeader prints the header for a single test
func (tr *TestReporting) PrintTestHeader(testID, testName string) {
	PrintTestHeader(testID, testName)
}

// PrintTestFooter prints the footer for a single test
func (tr *TestReporting) PrintTestFooter(testID, testName string, result TestResult) {
	PrintTestFooter(testID, testName, result.Status)
}

// PrintStepResult prints the result of a test step
func (tr *TestReporting) PrintStepResult(step TestStep) {
	PrintStepResult(step)
}

// PrintSummaryReport prints the complete summary report
func (tr *TestReporting) PrintSummaryReport() {
	summary := tr.GetSummary()

	PrintSeparator()
	PrintSummary(summary.TotalTests, summary.PassedTests, summary.FailedTests, summary.Duration)

	// Group results by status domains if verbose
	if tr.verbose {
		tr.printDetailedResults()
	}
}

// printDetailedResults prints detailed test results
func (tr *TestReporting) printDetailedResults() {
	tr.mu.RLock()
	defer tr.mu.RUnlock()

	// Group by test status
	passed := make([]TestResult, 0)
	failed := make([]TestResult, 0)
	errors := make([]TestResult, 0)
	skipped := make([]TestResult, 0)

	for _, result := range tr.testResults {
		switch result.Status {
		case TestStatusPass:
			passed = append(passed, result)
		case TestStatusFail:
			failed = append(failed, result)
		case TestStatusError:
			errors = append(errors, result)
		case TestStatusSkip:
			skipped = append(skipped, result)
		}
	}

	// Print failed tests
	if len(failed) > 0 {
		PrintSectionHeader("FAILED TESTS")
		for _, result := range failed {
			fmt.Printf("  ❌ %s: %s\n", result.ID, result.Name)
			for _, step := range result.TestSteps {
				if step.Status == TestStatusFail || step.Status == TestStatusError {
					fmt.Printf("    ❌ Step %d: %s - %s\n", step.Number, step.Name, step.Message)
				}
			}
		}
	}

	// Print error tests
	if len(errors) > 0 {
		PrintSectionHeader("ERROR TESTS")
		for _, result := range errors {
			fmt.Printf("  🚨 %s: %s\n", result.ID, result.Name)
			for _, step := range result.TestSteps {
				if step.Status == TestStatusError {
					fmt.Printf("    🚨 Step %d: %s - %s\n", step.Number, step.Name, step.Message)
				}
			}
		}
	}

	// Print skipped tests
	if len(skipped) > 0 && tr.verbose {
		PrintSectionHeader("SKIPPED TESTS")
		for _, result := range skipped {
			fmt.Printf("  ⏭️  %s: %s\n", result.ID, result.Name)
		}
	}

	// Print summary by category if we had domain information
	tr.printDomainSummary()
}

// printDomainSummary prints test summary by domain
func (tr *TestReporting) printDomainSummary() {
	domains := make(map[string][]TestResult)

	for _, result := range tr.testResults {
		// Extract domain from test ID (e.g., AUTH-01 -> auth)
		if len(result.ID) > 4 && result.ID[4] == '-' {
			domain := result.ID[:4]
			domains[domain] = append(domains[domain], result)
		}
	}

	if len(domains) > 1 {
		PrintSectionHeader("DOMAIN SUMMARY")
		for domain, results := range domains {
			passed := 0
			for _, result := range results {
				if result.Status == TestStatusPass {
					passed++
				}
			}
			fmt.Printf("  🏷️  %s: %d/%d tests passed\n", domain, passed, len(results))
		}
	}
}

// SaveReport saves the test report to a JSON file
func (tr *TestReporting) SaveReport(filename string) error {
	summary := tr.GetSummary()

	report := map[string]interface{}{
		"summary":      summary,
		"test_results": tr.GetTestResults(),
		"generated_at": time.Now(),
	}

	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal report: %w", err)
	}

	if err := os.WriteFile(filename, data, 0644); err != nil {
		return fmt.Errorf("failed to write report file: %w", err)
	}

	PrintInfo(fmt.Sprintf("Report saved to %s", filename))
	return nil
}

// TestSummary represents a summary of test execution
type TestSummary struct {
	TotalTests        int           `json:"total_tests"`
	PassedTests       int           `json:"passed_tests"`
	FailedTests       int           `json:"failed_tests"`
	ErrorTests        int           `json:"error_tests"`
	SkippedTests      int           `json:"skipped_tests"`
	TotalSteps        int           `json:"total_steps"`
	PassedSteps       int           `json:"passed_steps"`
	FailedSteps       int           `json:"failed_steps"`
	ErrorSteps        int           `json:"error_steps"`
	SkippedSteps      int           `json:"skipped_steps"`
	Duration          float64       `json:"duration"`
	StartTime         time.Time     `json:"start_time"`
	EndTime           *time.Time    `json:"end_time,omitempty"`
	TestSuccessRate   float64       `json:"test_success_rate"`
	StepSuccessRate   float64       `json:"step_success_rate"`
}

// WatchTestExecution watches test execution and provides real-time updates
func (tr *TestReporting) WatchTestExecution(ctx context.Context, testChan <-chan TestResult) {
	for {
		select {
		case <-ctx.Done():
			return
		case result, ok := <-testChan:
			if !ok {
				// Channel closed, execution finished
				tr.SetEndTime()
				return
			}
			tr.AddTestResult(result)
		}
	}
}