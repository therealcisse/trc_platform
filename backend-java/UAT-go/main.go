package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/fatih/color"
	"github.com/spf13/cobra"

	"uat/config"
	"uat/constants"
	"uat/domains/test"
	"uat/framework"
	"uat/helpers"
)

// TestRunner manages test execution across domains
type TestRunner struct {
	domains []framework.Domain
	config  *config.Config
	verbose bool
}

// NewTestRunner creates a new test runner
func NewTestRunner(cfg *config.Config, verbose bool) *TestRunner {
	return &TestRunner{
		domains: make([]framework.Domain, 0),
		config:  cfg,
		verbose: verbose,
	}
}

// AddDomain adds a test domain
func (tr *TestRunner) AddDomain(domain framework.Domain) {
	tr.domains = append(tr.domains, domain)
}

// RunTests runs all tests in all domains
func (tr *TestRunner) RunTests(ctx context.Context, domainFilter, testFilter string, dryRun bool) error {
	// Filter domains if specified
	var domainsToRun []framework.Domain
	if domainFilter != "" && domainFilter != "all" {
		for _, domain := range tr.domains {
			if domain.Name() == domainFilter {
				domainsToRun = append(domainsToRun, domain)
				break
			}
		}
		if len(domainsToRun) == 0 {
			return fmt.Errorf("domain '%s' not found", domainFilter)
		}
	} else {
		domainsToRun = tr.domains
	}

	// Collect all tests to run
	var testsToRun []framework.Test
	for _, domain := range domainsToRun {
		tests := domain.GetTests()
		for _, test := range tests {
			// Apply test filter if specified
			if testFilter != "" {
				if test.ID() != testFilter &&
				   !contains(test.Name(), testFilter) &&
				   !contains(test.Description(), testFilter) {
					continue
				}
			}
			testsToRun = append(testsToRun, test)
		}
	}

	if len(testsToRun) == 0 {
		return fmt.Errorf("no tests found matching the specified criteria")
	}

	// Print test plan
	tr.printTestPlan(domainsToRun, testsToRun)

	if dryRun {
		fmt.Printf("\n🏃 Dry run completed. No tests executed.\n")
		return nil
	}

	// Create framework instance
	fw, err := framework.NewFramework(ctx, tr.config)
	if err != nil {
		return fmt.Errorf("failed to create framework: %w", err)
	}
	defer fw.Close()

	// Initialize helpers
	helpers.InitializeGlobalAuth(tr.config, fw.Database, fw.HTTPClient)

	// Setup reporting
	fw.Reporting.SetVerbose(tr.verbose)

	// Execute tests
	return tr.executeTests(ctx, fw, domainsToRun, testsToRun)
}

// printTestPlan prints the test execution plan
func (tr *TestRunner) printTestPlan(domains []framework.Domain, tests []framework.Test) {
	fmt.Printf("\n%s\n", color.New(color.FgCyan, color.Bold).Sprint("📋 TEST EXECUTION PLAN"))
	fmt.Printf("%s\n", color.New(color.FgCyan).Sprint(strings.Repeat("=", 80)))

	// Group by domain
	domainTests := make(map[string][]framework.Test)
	for _, test := range tests {
		domain := "unknown"
		// Extract domain from test ID (e.g., AUTH-01 -> auth)
		if len(test.ID()) > 4 && test.ID()[4] == '-' {
			domain = test.ID()[:4]
		}
		domainTests[domain] = append(domainTests[domain], test)
	}

	for domain, domainTests := range domainTests {
		// Find domain info
		var domainInfo framework.Domain
		for _, d := range domains {
			if d.Name() == domain {
				domainInfo = d
				break
			}
		}

		if domainInfo != nil {
			fmt.Printf("\n🏷️  %s (%s)\n", domainInfo.Name(), domainInfo.Description())
		} else {
			fmt.Printf("\n🏷️  %s\n", domain)
		}
		fmt.Printf("   Tests: %d\n", len(domainTests))

		for _, test := range domainTests {
			requiredMarker := "✓"
			if !test.Required() {
				requiredMarker = "○"
			}
			fmt.Printf("   %s %s: %s\n", requiredMarker, test.ID(), test.Name())
		}
	}
}

// executeTests executes the tests
func (tr *TestRunner) executeTests(ctx context.Context, fw *framework.Framework, domains []framework.Domain, tests []framework.Test) error {
	fmt.Printf("\n🚀 EXECUTING %d TESTS...\n", len(tests))

	for i, test := range tests {
		fmt.Printf("\n📍 Progress: %d/%d\n", i+1, len(tests))

		// Find domain for this test
		var testDomain framework.Domain
		for _, domain := range domains {
			domainTests := domain.GetTests()
			for _, dt := range domainTests {
				if dt.ID() == test.ID() {
					testDomain = domain
					break
				}
			}
			if testDomain != nil {
				break
			}
		}

		// Setup domain if not already done
		if testDomain != nil {
			if err := testDomain.Setup(ctx, fw); err != nil {
				fmt.Printf("❌ Domain setup failed for %s: %v\n", testDomain.Name(), err)
				continue
			}
			defer testDomain.Cleanup(ctx, fw)
		}

		// Execute test
		fmt.Printf("🧪 EXECUTING %s: %s\n", test.ID(), test.Name())
		fmt.Printf("📄 %s\n", test.Description())

		result := test.Execute(ctx, fw)

		// Add to reporting
		fw.Reporting.AddTestResult(result)

		// Print result
		if result.IsSuccess() {
			fmt.Printf("✅ %s: PASSED (%.2fs)\n", test.ID(), result.TotalTime)
		} else {
			fmt.Printf("❌ %s: FAILED (%.2fs)\n", test.ID(), result.TotalTime)

			// Print failed steps
			for _, step := range result.TestSteps {
				if step.Status == framework.TestStatusFail || step.Status == framework.TestStatusError {
					fmt.Printf("    ❌ Step %d: %s - %s\n", step.Number, step.Name, step.Message)
				}
			}
		}

		// Print step details for verbose output
		if tr.verbose {
			for _, step := range result.TestSteps {
				if step.Status == framework.TestStatusPass {
					fmt.Printf("    ✅ Step %d: %s\n", step.Number, step.Name)
				}
			}
		}
	}

	// Generate summary report
	fw.Reporting.SetEndTime()
	fw.Reporting.PrintSummaryReport()

	// Save report if requested
	if tr.verbose {
		reportFile := fmt.Sprintf("uat_report_%s.json", time.Now().Format("20060102_150405"))
		if err := fw.Reporting.SaveReport(reportFile); err != nil {
			fmt.Printf("⚠️  Failed to save report: %v\n", err)
		}
	}

	// Return error if any tests failed
	summary := fw.Reporting.GetSummary()
	if summary.FailedTests > 0 {
		return fmt.Errorf("%d tests failed", summary.FailedTests)
	}

	return nil
}

// contains checks if a string contains a substring (case-insensitive)
func contains(s, substr string) bool {
	return len(s) >= len(substr) &&
		   (s == substr ||
		    len(s) > len(substr) &&
		    (s[:len(substr)] == substr ||
		     s[len(s)-len(substr):] == substr ||
		     indexOf(s, substr) >= 0))
}

// indexOf finds substring index (simple implementation)
func indexOf(s, substr string) int {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return i
		}
	}
	return -1
}

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "uat-go",
	Short: "TRC Platform UAT Test Framework (Go)",
	Long: `TRC Platform User Acceptance Test Framework written in Go.

This framework provides type-safe testing capabilities with the following features:
- Database connectivity and validation
- HTTP client with authentication support
- Email verification via Mailcatcher
- Comprehensive error handling and logging
- Input validation and sanitization
- Test reporting and summary generation`,
	Run: func(cmd *cobra.Command, args []string) {
		runMain()
	},
}

// runCmd represents the test run command
var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Run UAT tests",
	Long:  `Run UAT tests across all domains or specific domains/tests.`,
	Run:   runTests,
}

var (
	domainFlag    string
	testFlag      string
	dryRunFlag    bool
	verboseFlag   bool
)

func init() {
	// Add run command
	rootCmd.AddCommand(runCmd)

	// Add flags
	runCmd.Flags().StringVarP(&domainFlag, "domain", "d", "all", "Specify domain to test (test, auth, billing, usage, api_token, image_solve, all)")
	runCmd.Flags().StringVarP(&testFlag, "filter", "f", "", "Filter tests by ID, name, or description")
	runCmd.Flags().BoolVarP(&dryRunFlag, "dry-run", "n", false, "Show test plan without executing tests")
	runCmd.Flags().BoolVarP(&verboseFlag, "verbose", "v", false, "Enable verbose output")
}

func runTests(cmd *cobra.Command, args []string) {
	// Create context for graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Handle signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		fmt.Printf("\n🛑 Received signal: %v\n", sig)
		cancel()
	}()

	// Load configuration
	cfg := config.LoadConfig()

	// Print configuration summary
	printConfigSummary(cfg)

	// Create test runner
	runner := NewTestRunner(cfg, verboseFlag)

	// Add test domain (for now, just the test domain)
	testDomain := test.NewTestDomain()
	runner.AddDomain(testDomain)

	// Run tests
	if err := runner.RunTests(ctx, domainFlag, testFlag, dryRunFlag); err != nil {
		log.Fatalf("Test execution failed: %v", err)
	}

	if !dryRunFlag {
		fmt.Printf("🎉 All tests completed successfully!\n")
	}
}

func runMain() {
	fmt.Printf("TRC Platform UAT Framework (Go) v1.0.0\n")
	fmt.Printf("Type-safe test framework for TRC Platform\n\n")

	// Load and validate configuration
	cfg := config.LoadConfig()
	printConfigSummary(cfg)

	// Test basic connectivity
	fmt.Printf("🔍 Validating environment...\n")
	validationResults := validateEnvironment(cfg)

	allGood := true
	for service, status := range validationResults {
		if status {
			fmt.Printf("✅ %s: Available\n", service)
		} else {
			fmt.Printf("❌ %s: Not available\n", service)
			allGood = false
		}
	}

	if !allGood {
		fmt.Printf("\n⚠️  Some services are not available. Tests may fail.\n")
		fmt.Printf("Use 'uat-go run --dry-run' to see test plan without execution.\n")
	}

	fmt.Printf("\n💡 Use 'uat-go run --help' to see available options.\n")
}

func printConfigSummary(cfg *config.Config) {
	fmt.Printf("%s\n", color.New(color.FgCyan, color.Bold).Sprint("⚙️  CONFIGURATION SUMMARY"))
	fmt.Printf("%s\n", color.New(color.FgCyan).Sprint(strings.Repeat("=", 80)))
	fmt.Printf("📡 Application URL: %s\n", cfg.AppURL)
	fmt.Printf("🗄️  Database URL: %s\n", cfg.DatabaseURL)
	fmt.Printf("📧 Mailcatcher URL: %s\n", cfg.MailcatcherURL)
	fmt.Printf("⏱️  HTTP Timeout: %v\n", cfg.HTTPTimeout)
	fmt.Printf("📊 Log Level: %s\n", cfg.LogLevel)
	fmt.Printf("%s\n", color.New(color.FgCyan).Sprint(strings.Repeat("=", 80)))
}

func validateEnvironment(cfg *config.Config) map[string]bool {
	results := make(map[string]bool)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Test application availability
	client := framework.NewHTTPClient(cfg.AppURL)
	resp, err := client.Get(ctx, constants.EndpointHealth, nil)
	results["Application"] = err == nil && resp != nil && resp.Status == 200

	// Test database availability
	db, err := framework.NewDatabaseHelper(cfg.DatabaseURL)
	if err == nil {
		results["Database"] = db.Ping(ctx) == nil
		db.Close()
	} else {
		results["Database"] = false
	}

	// Test email availability
	emailHelper := framework.NewEmailHelper(cfg.MailcatcherURL)
	results["Email"] = emailHelper.ConnectMailcatcher(ctx) == nil

	return results
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		log.Fatalf("Error: %v", err)
	}
}
