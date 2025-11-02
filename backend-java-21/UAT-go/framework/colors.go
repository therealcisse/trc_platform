package framework

import (
	"fmt"
	"strings"

	"github.com/fatih/color"
)

// Color definitions for console output
var (
	// Success colors
	SuccessColor = color.New(color.FgGreen).SprintFunc()
	SuccessBold  = color.New(color.FgGreen, color.Bold).SprintFunc()

	// Error colors
	ErrorColor = color.New(color.FgRed).SprintFunc()
	ErrorBold  = color.New(color.FgRed, color.Bold).SprintFunc()

	// Warning colors
	WarningColor = color.New(color.FgYellow).SprintFunc()
	WarningBold  = color.New(color.FgYellow, color.Bold).SprintFunc()

	// Info colors
	InfoColor = color.New(color.FgBlue).SprintFunc()
	InfoBold  = color.New(color.FgBlue, color.Bold).SprintFunc()

	// Test status colors
	PassColor = color.New(color.FgGreen).SprintFunc()
	FailColor = color.New(color.FgRed).SprintFunc()
	SkipColor = color.New(color.FgYellow).SprintFunc()

	// Header colors
	HeaderColor = color.New(color.FgCyan, color.Bold).SprintFunc()
	HeaderBold  = color.New(color.FgCyan, color.Bold).SprintFunc()

	// Muted colors
	MutedColor = color.New(color.Faint).SprintFunc()
)

// Helper function to repeat strings
func repeat(s string, count int) string {
	return strings.Repeat(s, count)
}

// PrintSuccess prints a success message with green color
func PrintSuccess(message string) {
	fmt.Printf("%s ✅ %s\n", SuccessBold("[SUCCESS]"), message)
}

// PrintError prints an error message with red color
func PrintError(message string) {
	fmt.Printf("%s ❌ %s\n", ErrorBold("[ERROR]"), message)
}

// PrintWarning prints a warning message with yellow color
func PrintWarning(message string) {
	fmt.Printf("%s ⚠️  %s\n", WarningBold("[WARNING]"), message)
}

// PrintInfo prints an info message with blue color
func PrintInfo(message string) {
	fmt.Printf("%s ℹ️  %s\n", InfoBold("[INFO]"), message)
}

// PrintTestHeader prints a test header with cyan color
func PrintTestHeader(testID, testName string) {
	fmt.Printf("\n%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("🧪 STARTING %s: %s\n", HeaderBold(testID), HeaderColor(testName))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
}

// PrintTestFooter prints a test footer with appropriate coloring
func PrintTestFooter(testID, testName string, status TestStatus) {
	var statusColor func(a ...interface{}) string
	var statusIcon string

	switch status {
	case TestStatusPass:
		statusColor = SuccessBold
		statusIcon = "✅"
	case TestStatusFail:
		statusColor = ErrorBold
		statusIcon = "❌"
	case TestStatusSkip:
		statusColor = WarningBold
		statusIcon = "⏭️"
	case TestStatusError:
		statusColor = ErrorBold
		statusIcon = "🚨"
	default:
		statusColor = MutedColor
		statusIcon = "❓"
	}

	fmt.Printf("\n%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s %s: %s - %s\n", statusIcon, testID, testName, statusColor(string(status)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
}

// PrintStepResult prints a test step result
func PrintStepResult(step TestStep) {
	var statusColor func(a ...interface{}) string
	var statusIcon string

	switch step.Status {
	case TestStatusPass:
		statusColor = SuccessColor
		statusIcon = "✅"
	case TestStatusFail:
		statusColor = ErrorColor
		statusIcon = "❌"
	case TestStatusSkip:
		statusColor = WarningColor
		statusIcon = "⏭️"
	case TestStatusError:
		statusColor = ErrorColor
		statusIcon = "🚨"
	default:
		statusColor = MutedColor
		statusIcon = "❓"
	}

	timeInfo := ""
	if step.ResponseTime > 0 {
		timeInfo = fmt.Sprintf(" (%v)", step.ResponseTime)
	}

	fmt.Printf("  %d. %s - %s%s", step.Number, step.Name, statusColor(string(step.Status)), timeInfo)
	if step.Message != "" {
		fmt.Printf(" - %s", step.Message)
	}
	if statusIcon != "" {
		fmt.Printf(" [%s]", statusIcon)
	}
	fmt.Printf("\n")
}

// PrintSectionHeader prints a section header
func PrintSectionHeader(title string) {
	fmt.Printf("\n# %s\n", HeaderBold(title))
	fmt.Printf("%s\n", HeaderColor(repeat("=", len(title)+4)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", len(title)+4)))
}

// PrintSeparator prints a separator line
func PrintSeparator() {
	fmt.Printf("%s\n", MutedColor(repeat("-", 80)))
}

// PrintProgressBar prints a progress bar
func PrintProgressBar(current, total int, description string) {
	percentage := float64(current) / float64(total)
	barWidth := 50
	filledWidth := int(percentage * float64(barWidth))

	bar := ""
	for i := 0; i < barWidth; i++ {
		if i < filledWidth {
			bar += "█"
		} else {
			bar += "░"
		}
	}

	fmt.Printf("\r%s [%s] %d/%d (%.1f%%)", description, SuccessColor(bar), current, total, percentage*100)
	if current == total {
		fmt.Printf("\n")
	}
}

// PrintSummary prints a summary report
func PrintSummary(totalTests, passedTests, failedTests int, duration float64) {
	successRate := float64(passedTests) / float64(totalTests) * 100

	fmt.Printf("\n%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("📊 UAT TEST EXECUTION REPORT\n")
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
	fmt.Printf("📊 Duration: %.2f seconds\n", duration)
	fmt.Printf("📊 Tests Total: %d\n", totalTests)
	fmt.Printf("✅ Passed: %s\n", SuccessBold(fmt.Sprintf("%d", passedTests)))
	fmt.Printf("❌ Failed: %s\n", ErrorBold(fmt.Sprintf("%d", failedTests)))
	fmt.Printf("📈 Success Rate: ")
	if successRate >= 90 {
		fmt.Printf("%s", SuccessBold(fmt.Sprintf("%.1f%%", successRate)))
	} else if successRate >= 70 {
		fmt.Printf("%s", WarningBold(fmt.Sprintf("%.1f%%", successRate)))
	} else {
		fmt.Printf("%s", ErrorBold(fmt.Sprintf("%.1f%%", successRate)))
	}
	fmt.Printf("\n")
	fmt.Printf("%s\n", HeaderColor(repeat("=", 80)))
}