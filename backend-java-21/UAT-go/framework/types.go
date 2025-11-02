package framework

import (
	"context"
	"time"

	"uat/config"
)

// TestStatus represents the status of a test or test step
type TestStatus string

const (
	TestStatusPass    TestStatus = "PASS"
	TestStatusFail    TestStatus = "FAIL"
	TestStatusSkip    TestStatus = "SKIP"
	TestStatusError   TestStatus = "ERROR"
	TestStatusRunning TestStatus = "RUNNING"
)

// TestStep represents an individual test step result
type TestStep struct {
	Number       int           `json:"number"`
	Name         string        `json:"name"`
	Status       TestStatus    `json:"status"`
	Message      string        `json:"message"`
	ResponseTime time.Duration `json:"response_time"`
	RequestData  interface{}   `json:"request_data,omitempty"`
	ResponseData interface{}   `json:"response_data,omitempty"`
	Screenshots  []string      `json:"screenshots,omitempty"`
}

// IsSuccess returns true if the test step was successful
func (ts TestStep) IsSuccess() bool {
	return ts.Status == TestStatusPass || ts.Status == TestStatusSkip
}

// TestResult represents the complete result of a test
type TestResult struct {
	ID           string       `json:"id"`
	Name         string       `json:"name"`
	Status       TestStatus   `json:"status"`
	TotalSteps   int          `json:"total_steps"`
	PassedSteps  int          `json:"passed_steps"`
	FailedSteps  int          `json:"failed_steps"`
	SkippedSteps int          `json:"skipped_steps"`
	ErrorSteps   int          `json:"error_steps"`
	TotalTime    float64      `json:"total_time"`
	StartTime    time.Time    `json:"start_time"`
	EndTime      *time.Time   `json:"end_time,omitempty"`
	TestSteps    []TestStep   `json:"test_steps"`
	EvidenceFiles []string    `json:"evidence_files,omitempty"`
	Environment  Environment  `json:"environment"`
}

// IsSuccess returns true if the test was successful
func (tr TestResult) IsSuccess() bool {
	return tr.Status == TestStatusPass
}

// GetSuccessRate returns the success rate as a percentage
func (tr TestResult) GetSuccessRate() float64 {
	if tr.TotalSteps == 0 {
		return 0.0
	}
	return (float64(tr.PassedSteps) / float64(tr.TotalSteps)) * 100
}

// Environment represents environment information
type Environment struct {
	AppURL          string `json:"app_url"`
	DatabaseURL     string `json:"database_url"`
	MailcatcherURL  string `json:"mailcatcher_url"`
	AppStatus       string `json:"app_status"`
	DatabaseStatus  string `json:"database_status"`
	MailcatcherStatus string `json:"mailcatcher_status"`
	JavaVersion     string `json:"java_version,omitempty"`
	SpringProfile   string `json:"spring_profile,omitempty"`
}

// Framework represents the main test framework
type Framework struct {
	Config     *config.Config
	Database   *DatabaseHelper
	HTTPClient *HTTPClient
	Email      *EmailHelper
	Reporting  *TestReporting
}

// NewFramework creates a new test framework instance
func NewFramework(ctx context.Context, cfg *config.Config) (*Framework, error) {
	fw := &Framework{
		Config:    cfg,
		Reporting: NewTestReporting(),
	}

	// Initialize database helper
	db, err := NewDatabaseHelper(cfg.GetDatabaseURL())
	if err != nil {
		return nil, err
	}
	fw.Database = db

	// Initialize HTTP client
	fw.HTTPClient = NewHTTPClient(cfg.GetAppURL())

	// Initialize email helper
	fw.Email = NewEmailHelper(cfg.GetMailcatcherURL())

	return fw, nil
}

// Close cleans up framework resources
func (fw *Framework) Close() error {
	if fw.Database != nil {
		return fw.Database.Close()
	}
	return nil
}

// Test interface represents a test that can be executed
type Test interface {
	ID() string
	Name() string
	Description() string
	Priority() int
	Required() bool
	Execute(ctx context.Context, fw *Framework) TestResult
}

// Domain interface represents a test domain
type Domain interface {
	Name() string
	Description() string
	Setup(ctx context.Context, fw *Framework) error
	Cleanup(ctx context.Context, fw *Framework) error
	GetTests() []Test
}
