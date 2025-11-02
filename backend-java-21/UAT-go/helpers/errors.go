package helpers

import (
	"fmt"
	"runtime"
	"strings"
	"time"

	"uat/framework"
)

// ErrorCategory represents the category of an error
type ErrorCategory int

const (
	ErrorCategorySystem ErrorCategory = iota
	ErrorCategoryAuthentication
	ErrorCategoryDatabase
	ErrorCategoryNetwork
	ErrorCategoryValidation
	ErrorCategoryConfiguration
	ErrorCategoryTest
)

// ErrorSeverity represents the severity of an error
type ErrorSeverity int

const (
	ErrorSeverityLow ErrorSeverity = iota
	ErrorSeverityMedium
	ErrorSeverityHigh
	ErrorSeverityCritical
)

// String returns the string representation of ErrorCategory
func (ec ErrorCategory) String() string {
	switch ec {
	case ErrorCategorySystem:
		return "system"
	case ErrorCategoryAuthentication:
		return "authentication"
	case ErrorCategoryDatabase:
		return "database"
	case ErrorCategoryNetwork:
		return "network"
	case ErrorCategoryValidation:
		return "validation"
	case ErrorCategoryConfiguration:
		return "configuration"
	case ErrorCategoryTest:
		return "test"
	default:
		return "unknown"
	}
}

// String returns the string representation of ErrorSeverity
func (es ErrorSeverity) String() string {
	switch es {
	case ErrorSeverityLow:
		return "low"
	case ErrorSeverityMedium:
		return "medium"
	case ErrorSeverityHigh:
		return "high"
	case ErrorSeverityCritical:
		return "critical"
	default:
		return "unknown"
	}
}

// ErrorContext provides context information for errors
type ErrorContext struct {
	Operation     string                 `json:"operation"`
	Component     string                 `json:"component"`
	UserID        string                 `json:"user_id,omitempty"`
	RequestID     string                 `json:"request_id,omitempty"`
	AdditionalData map[string]interface{} `json:"additional_data,omitempty"`
}

// UATError represents a structured error in the UAT framework
type UATError struct {
	ID          string        `json:"id"`
	Category    ErrorCategory `json:"category"`
	Severity    ErrorSeverity `json:"severity"`
	Message     string        `json:"message"`
	Context     *ErrorContext `json:"context,omitempty"`
	Timestamp   time.Time     `json:"timestamp"`
	StackTrace  string        `json:"stack_trace,omitempty"`
	RetryCount  int           `json:"retry_count"`
	MaxRetries  int           `json:"max_retries"`
	Cause       error         `json:"cause,omitempty"`
}

// Error implements the error interface
func (ue *UATError) Error() string {
	return ue.Message
}

// Unwrap returns the underlying cause
func (ue *UATError) Unwrap() error {
	return ue.Cause
}

// ErrorHandler handles error logging and management
type ErrorHandler struct {
	errors          []UATError
	errorCallbacks  map[ErrorCategory][]func(UATError)
	maxLogSize      int
	nextErrorID     int
}

// NewErrorHandler creates a new error handler
func NewErrorHandler() *ErrorHandler {
	return &ErrorHandler{
		errors:         make([]UATError, 0),
		errorCallbacks: make(map[ErrorCategory][]func(UATError)),
		maxLogSize:     1000,
		nextErrorID:    1,
	}
}

// HandleError handles an error with consistent logging
func (eh *ErrorHandler) HandleError(err error, category ErrorCategory, severity ErrorSeverity, context *ErrorContext) *UATError {
	errorID := eh.generateErrorID()

	uatErr := &UATError{
		ID:         errorID,
		Category:   category,
		Severity:   severity,
		Message:    err.Error(),
		Context:    context,
		Timestamp:  time.Now(),
		StackTrace: eh.getStackTrace(),
		RetryCount: 0,
		MaxRetries: 3,
		Cause:      err,
	}

	// Log error
	eh.logError(uatErr)

	// Store in error log
	eh.storeError(uatErr)

	// Trigger callbacks
	eh.triggerCallbacks(uatErr)

	return uatErr
}

// HandleErrorWithRetry handles an error with retry capability
func (eh *ErrorHandler) HandleErrorWithRetry(err error, category ErrorCategory, severity ErrorSeverity, context *ErrorContext, retryCount, maxRetries int) *UATError {
	errorID := eh.generateErrorID()

	uatErr := &UATError{
		ID:         errorID,
		Category:   category,
		Severity:   severity,
		Message:    err.Error(),
		Context:    context,
		Timestamp:  time.Now(),
		StackTrace: eh.getStackTrace(),
		RetryCount: retryCount,
		MaxRetries: maxRetries,
		Cause:      err,
	}

	// Log error
	eh.logError(uatErr)

	// Store in error log
	eh.storeError(uatErr)

	// Trigger callbacks
	eh.triggerCallbacks(uatErr)

	return uatErr
}

// RegisterCallback registers a callback for specific error categories
func (eh *ErrorHandler) RegisterCallback(category ErrorCategory, callback func(UATError)) {
	if eh.errorCallbacks[category] == nil {
		eh.errorCallbacks[category] = make([]func(UATError), 0)
	}
	eh.errorCallbacks[category] = append(eh.errorCallbacks[category], callback)
}

// GetErrorsByCategory returns errors by category
func (eh *ErrorHandler) GetErrorsByCategory(category ErrorCategory) []UATError {
	var result []UATError
	for _, err := range eh.errors {
		if err.Category == category {
			result = append(result, err)
		}
	}
	return result
}

// GetErrorsBySeverity returns errors by severity
func (eh *ErrorHandler) GetErrorsBySeverity(severity ErrorSeverity) []UATError {
	var result []UATError
	for _, err := range eh.errors {
		if err.Severity == severity {
			result = append(result, err)
		}
	}
	return result
}

// GetErrorSummary returns a summary of errors
func (eh *ErrorHandler) GetErrorSummary() map[string]interface{} {
	summary := map[string]interface{}{
		"total_errors": len(eh.errors),
		"by_category":  make(map[string]int),
		"by_severity":  make(map[string]int),
	}

	for _, err := range eh.errors {
		// Count by category
		category := err.Category.String()
		byCategory := summary["by_category"].(map[string]int)
		byCategory[category]++

		// Count by severity
		severity := err.Severity.String()
		bySeverity := summary["by_severity"].(map[string]int)
		bySeverity[severity]++
	}

	return summary
}

// ClearErrorLog clears the error log
func (eh *ErrorHandler) ClearErrorLog() {
	eh.errors = make([]UATError, 0)
}

// generateErrorID generates a unique error ID
func (eh *ErrorHandler) generateErrorID() string {
	id := eh.nextErrorID
	eh.nextErrorID++
	return fmt.Sprintf("ERR_%08X", id)
}

// logError logs error with appropriate level based on severity
func (eh *ErrorHandler) logError(err *UATError) {
	prefix := fmt.Sprintf("[%s] [%s]", err.ID, strings.ToUpper(err.Category.String()))

	if err.Context != nil {
		prefix += fmt.Sprintf(" [%s:%s]", err.Context.Component, err.Context.Operation)
	}

	message := fmt.Sprintf("%s %s", prefix, err.Message)

	switch err.Severity {
	case ErrorSeverityCritical:
		framework.PrintError(fmt.Sprintf("🚨 CRITICAL: %s", message))
		if err.StackTrace != "" {
			framework.PrintError(fmt.Sprintf("Stack trace:\n%s", err.StackTrace))
		}
	case ErrorSeverityHigh:
		framework.PrintError(fmt.Sprintf("❌ HIGH: %s", message))
	case ErrorSeverityMedium:
		framework.PrintWarning(fmt.Sprintf("⚠️ MEDIUM: %s", message))
	case ErrorSeverityLow:
		framework.PrintInfo(fmt.Sprintf("ℹ️ LOW: %s", message))
	}
}

// storeError stores error in log with size limit
func (eh *ErrorHandler) storeError(err *UATError) {
	eh.errors = append(eh.errors, *err)

	// Maintain maximum log size
	if len(eh.errors) > eh.maxLogSize {
		eh.errors = eh.errors[len(eh.errors)-eh.maxLogSize:]
	}
}

// triggerCallbacks triggers registered error callbacks
func (eh *ErrorHandler) triggerCallbacks(err *UATError) {
	callbacks := eh.errorCallbacks[err.Category]
	for _, callback := range callbacks {
		go func(cb func(UATError)) {
			defer func() {
				if r := recover(); r != nil {
					framework.PrintError(fmt.Sprintf("Error in error callback: %v", r))
				}
			}()
			cb(*err)
		}(callback)
	}
}

// getStackTrace gets the current stack trace
func (eh *ErrorHandler) getStackTrace() string {
	buf := make([]byte, 1024)
	for {
		n := runtime.Stack(buf, false)
		if n < len(buf) {
			return string(buf[:n])
		}
		buf = make([]byte, 2*len(buf))
	}
}

// CreateErrorContext creates an error context with additional data
func CreateErrorContext(operation, component string, additionalData map[string]interface{}) *ErrorContext {
	return &ErrorContext{
		Operation:      operation,
		Component:      component,
		AdditionalData: additionalData,
	}
}

// Global error handler instance
var GlobalErrorHandler = NewErrorHandler()

// Convenience functions

// HandleDatabaseError handles database-related errors
func HandleDatabaseError(err error, operation string, context *ErrorContext) *UATError {
	if context == nil {
		context = CreateErrorContext(operation, "database", nil)
	}
	return GlobalErrorHandler.HandleError(err, ErrorCategoryDatabase, ErrorSeverityHigh, context)
}

// HandleNetworkError handles network-related errors
func HandleNetworkError(err error, operation string, context *ErrorContext) *UATError {
	if context == nil {
		context = CreateErrorContext(operation, "network", nil)
	}
	return GlobalErrorHandler.HandleError(err, ErrorCategoryNetwork, ErrorSeverityMedium, context)
}

// HandleValidationError handles validation errors
func HandleValidationError(err error, operation string, context *ErrorContext) *UATError {
	if context == nil {
		context = CreateErrorContext(operation, "validation", nil)
	}
	return GlobalErrorHandler.HandleError(err, ErrorCategoryValidation, ErrorSeverityMedium, context)
}

// HandleAuthenticationError handles authentication errors
func HandleAuthenticationError(err error, operation string, context *ErrorContext) *UATError {
	if context == nil {
		context = CreateErrorContext(operation, "authentication", nil)
	}
	return GlobalErrorHandler.HandleError(err, ErrorCategoryAuthentication, ErrorSeverityHigh, context)
}

// HandleConfigurationError handles configuration errors
func HandleConfigurationError(err error, operation string, context *ErrorContext) *UATError {
	if context == nil {
		context = CreateErrorContext(operation, "configuration", nil)
	}
	return GlobalErrorHandler.HandleError(err, ErrorCategoryConfiguration, ErrorSeverityCritical, context)
}
