package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"uat/constants"
)

// Config represents the UAT configuration
type Config struct {
	// Environment configuration
	AppURL        string
	DatabaseURL   string
	MailcatcherURL string

	// Timing and timeouts
	HTTPTimeout    time.Duration
	EmailTimeout   time.Duration
	DatabaseTimeout time.Duration

	// Admin configuration
	AdminEmail    string
	AdminPassword string

	// Test user configuration
	TestEmailDomain   string
	TestPasswordBase  string

	// JWT configuration
	JWTAlgorithm string
	JWTIssuer    string

	// API Token configuration
	APITokenPrefix         string
	APITokenLength        int
	TokenExpirationDays   int

	// Billing configuration
	BillingCostPerRequest int
	BillingTimezone       string

	// Usage configuration
	UsageDefaultPageSize    int
	UsageMaxPageSize        int
	UsageRequestLogRetentionDays int

	// Logging
	LogLevel string

	// Test execution
	MaxRetryAttempts int
	RetryDelay       time.Duration

	// Usage supported services
	UsageSupportedServices []string
	UsageDefaultSort       string
	UsageDefaultSortDirection string
}

// LoadConfig loads configuration from environment variables with defaults
func LoadConfig() *Config {
	config := &Config{
		// Environment configuration
		AppURL:         getEnvOrDefault("UAT_APP_URL", "http://localhost:8080"),
		DatabaseURL:    getEnvOrDefault("UAT_DATABASE_URL", "postgresql://trc_user:trc_password@localhost:5432/trc_platform"),
		MailcatcherURL: getEnvOrDefault("UAT_MAILCATCHER_URL", "http://localhost:1080"),

		// Timing and timeouts
		HTTPTimeout:      getDurationEnvOrDefault("UAT_HTTP_TIMEOUT", 60*time.Second),
		EmailTimeout:     getDurationEnvOrDefault("UAT_EMAIL_TIMEOUT", 30*time.Second),
		DatabaseTimeout:  getDurationEnvOrDefault("UAT_DATABASE_TIMEOUT", 10*time.Second),

		// Admin configuration
		AdminEmail:    getEnvOrDefault("UAT_ADMIN_EMAIL", "admin@trc-platform.local"),
		AdminPassword: os.Getenv("UAT_ADMIN_PASSWORD"), // Required

		// Test user configuration
		TestEmailDomain:  getEnvOrDefault("UAT_TEST_EMAIL_DOMAIN", "uat-test.trc-platform.local"),
		TestPasswordBase: os.Getenv("UAT_TEST_PASSWORD"), // Will generate if not provided

		// JWT configuration
		JWTAlgorithm: getEnvOrDefault("UAT_JWT_ALGORITHM", "HS256"),
		JWTIssuer:    getEnvOrDefault("UAT_JWT_ISSUER", "trc-platform"),

		// API Token configuration
		APITokenPrefix:       getEnvOrDefault("UAT_API_TOKEN_PREFIX", "tok_"),
		APITokenLength:       getIntEnvOrDefault("UAT_API_TOKEN_LENGTH", 47),
		TokenExpirationDays:  getIntEnvOrDefault("UAT_TOKEN_EXPIRATION_DAYS", 30),

		// Billing configuration
		BillingCostPerRequest: getIntEnvOrDefault("UAT_BILLING_COST_PER_REQUEST", 50),
		BillingTimezone:       getEnvOrDefault("UAT_BILLING_TIMEZONE", "Europe/Berlin"),

		// Usage configuration
		UsageDefaultPageSize:         getIntEnvOrDefault("UAT_USAGE_DEFAULT_PAGE_SIZE", 25),
		UsageMaxPageSize:             getIntEnvOrDefault("UAT_USAGE_MAX_PAGE_SIZE", 100),
		UsageRequestLogRetentionDays: getIntEnvOrDefault("UAT_USAGE_REQUEST_LOG_RETENTION_DAYS", 90),

		// Logging
		LogLevel: getEnvOrDefault("UAT_LOG_LEVEL", "INFO"),

		// Test execution
		MaxRetryAttempts: getIntEnvOrDefault("UAT_MAX_RETRY_ATTEMPTS", 3),
		RetryDelay:       getDurationEnvOrDefault("UAT_RETRY_DELAY", 1*time.Second),

		// Usage configuration
		UsageSupportedServices: []string{
			"core.image_solve",
			"core.text_solve",
			"core.analysis",
			"core.processing",
		},
		UsageDefaultSort:        getEnvOrDefault("UAT_USAGE_DEFAULT_SORT", "requestTs"),
		UsageDefaultSortDirection: getEnvOrDefault("UAT_USAGE_DEFAULT_SORT_DIRECTION", "desc"),
	}

	// Generate test password if not provided
	if config.TestPasswordBase == "" {
		config.TestPasswordBase = generateSecurePassword()
	}

	// Validate required configuration
	if config.AdminPassword == "" {
		panic("UAT_ADMIN_PASSWORD environment variable is required")
	}

	return config
}

func (c *Config) GetEndpoint(endpointName string) (string, error) {
    return c._GetEndpoint(endpointName, nil)
}

// GetEndpoint returns the full endpoint URL with optional parameter substitution
func (c *Config) _GetEndpoint(endpointName string, params map[string]string) (string, error) {
	var endpointPath string

    if params == nil {
        params = map[string]string{}
    }

	switch endpointName {
	case "login":
		endpointPath = constants.EndpointLogin
	case "user_register":
		endpointPath = constants.EndpointUserRegister
	case "admin_invites":
		endpointPath = constants.EndpointAdminInvites
	case "api_tokens":
		endpointPath = constants.EndpointAPITokens
	case "core_solve":
		endpointPath = constants.EndpointCoreSolve
	case "core_test_solve":
		endpointPath = constants.EndpointCoreTestSolve
	case "billing_current":
		endpointPath = constants.EndpointBillingCurrent
	case "billing_periods":
		endpointPath = constants.EndpointBillingPeriods
	case "billing_period_detail":
		endpointPath = constants.EndpointBillingPeriodDetail
	case "billing_history":
		endpointPath = constants.EndpointBillingHistory
	case "usage_summary":
		endpointPath = constants.EndpointUsageSummary
	case "usage_requests":
		endpointPath = constants.EndpointUsageRequests
	case "admin_billing_list":
		endpointPath = constants.EndpointAdminBillingList
	case "admin_billing_mark_paid":
		endpointPath = constants.EndpointAdminMarkPaid
	case "admin_billing_mark_overdue":
		endpointPath = constants.EndpointAdminMarkOverdue
	case "admin_billing_waive":
		endpointPath = constants.EndpointAdminWaive
	case "email_verify":
		endpointPath = constants.EndpointEmailVerify
	case "email_resend":
		endpointPath = constants.EndpointEmailResend
	case "password_change":
		endpointPath = constants.EndpointPasswordChange
	case "users_me":
		endpointPath = constants.EndpointUsersMe
	case "health":
		endpointPath = constants.EndpointHealth
	default:
		return "", fmt.Errorf("unknown endpoint: %s", endpointName)
	}

	// Simple parameter substitution (for {periodId} etc.)
	if params != nil {
		for _, value := range params {
			endpointPath = fmt.Sprintf(endpointPath, value)
		}
	}

	return endpointPath, nil
}

// GetAuthHeaders returns headers with JWT authentication
func (c *Config) GetAuthHeaders(token string) map[string]string {
	return map[string]string{
		"Content-Type":  "application/json",
		"Accept":        "application/json",
		"User-Agent":    "TRC-Platform-UAT-Go/1.0.0",
		"Authorization": fmt.Sprintf("Bearer %s", token),
	}
}

// GetAPITokenHeaders returns headers with API token authentication
func (c *Config) GetAPITokenHeaders(apiToken string) map[string]string {
	return map[string]string{
		"Content-Type": "application/json",
		"Accept":       "application/json",
		"User-Agent":   "TRC-Platform-UAT-Go/1.0.0",
		"Authorization": fmt.Sprintf("Bearer %s", apiToken),
	}
}

// Helper functions

func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getIntEnvOrDefault(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getDurationEnvOrDefault(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return time.Duration(intValue) * time.Second
		}
	}
	return defaultValue
}

func generateSecurePassword() string {
	// Generate a 16-character password with all required character types
	chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*"
	password := make([]byte, 16)

	// Ensure at least one of each required character type
	password[0] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[time.Now().Nanosecond()%26]
	password[1] = "abcdefghijklmnopqrstuvwxyz"[time.Now().Nanosecond()%26]
	password[2] = "0123456789"[time.Now().Nanosecond()%10]
	password[3] = "!@#$%^&*"[time.Now().Nanosecond()%8]

	// Fill the rest with random characters
	for i := 4; i < 16; i++ {
		password[i] = chars[time.Now().Nanosecond()%len(chars)]
	}

	return string(password)
}

// GetAppURL returns the application URL
func (c *Config) GetAppURL() string {
	return c.AppURL
}

// GetDatabaseURL returns the database URL
func (c *Config) GetDatabaseURL() string {
	return c.DatabaseURL
}

// GetMailcatcherURL returns the mailcatcher URL
func (c *Config) GetMailcatcherURL() string {
	return c.MailcatcherURL
}
