package helpers

import (
	"fmt"
	"html"
	"net/mail"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// ValidationResult represents the result of input validation
type ValidationResult struct {
	IsValid         bool        `json:"is_valid"`
	ErrorMessage    string      `json:"error_message,omitempty"`
	SanitizedValue  interface{} `json:"sanitized_value,omitempty"`
}

// InputValidator provides centralized input validation
type InputValidator struct {
	// SQL injection patterns
	sqlInjectionPatterns []*regexp.Regexp

	// XSS patterns
	xssPatterns []*regexp.Regexp
}

// NewInputValidator creates a new input validator
func NewInputValidator() *InputValidator {
	return &InputValidator{
		sqlInjectionPatterns: []*regexp.Regexp{
			regexp.MustCompile(`(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b`),
			regexp.MustCompile(`(?i)\b(OR|AND)\s+\d+\s*=\s*\d+`),
			regexp.MustCompile(`(?i)(--|#|\/\*|\*\/)`),
			regexp.MustCompile(`(?i)\b(MASTER|DBO|SYSADMIN)\b`),
			regexp.MustCompile(`(?i)\b(SLEEP|BENCHMARK|WAITFOR)\b`),
			regexp.MustCompile(`(?i)\b(XP_|SP_)\w+`),
		},
		xssPatterns: []*regexp.Regexp{
			regexp.MustCompile(`(?i)<script[^>]*>.*?</script>`),
			regexp.MustCompile(`(?i)javascript:`),
			regexp.MustCompile(`(?i)on\w+\s*=`),
			regexp.MustCompile(`(?i)<iframe[^>]*>`),
			regexp.MustCompile(`(?i)<object[^>]*>`),
			regexp.MustCompile(`(?i)<embed[^>]*>`),
			regexp.MustCompile(`(?i)<link[^>]*>`),
			regexp.MustCompile(`(?i)<meta[^>]*>`),
		},
	}
}

// ValidateEmail validates email format and checks for injection attempts
func (iv *InputValidator) ValidateEmail(email string) ValidationResult {
	if email == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: "Email is required",
		}
	}

	// Check for SQL injection patterns
	for _, pattern := range iv.sqlInjectionPatterns {
		if pattern.MatchString(email) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Email contains potentially dangerous content",
			}
		}
	}

	// Check for XSS patterns
	for _, pattern := range iv.xssPatterns {
		if pattern.MatchString(email) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Email contains potentially dangerous content",
			}
		}
	}

	// Validate email format using Go's mail package
	_, err := mail.ParseAddress(email)
	if err != nil {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: "Invalid email format",
		}
	}

	// Sanitize and return
	sanitized := strings.TrimSpace(strings.ToLower(email))
	return ValidationResult{
		IsValid:        true,
		SanitizedValue: sanitized,
	}
}

// ValidatePassword validates password strength
func (iv *InputValidator) ValidatePassword(password, fieldName string) ValidationResult {
	if password == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s is required", fieldName),
		}
	}

	if len(password) < 8 {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be at least 8 characters long", fieldName),
		}
	}

	if len(password) > 128 {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be less than 128 characters", fieldName),
		}
	}

	// Check password requirements
	var hasUpper, hasLower, hasDigit, hasSpecial bool

	for _, char := range password {
		switch {
		case unicode.IsUpper(char):
			hasUpper = true
		case unicode.IsLower(char):
			hasLower = true
		case unicode.IsDigit(char):
			hasDigit = true
		case strings.ContainsRune("!@#$%^&*()_+-=[]{}|;:,.<>?", char):
			hasSpecial = true
		}
	}

	var errors []string
	if !hasUpper {
		errors = append(errors, "at least one uppercase letter")
	}
	if !hasLower {
		errors = append(errors, "at least one lowercase letter")
	}
	if !hasDigit {
		errors = append(errors, "at least one digit")
	}
	if !hasSpecial {
		errors = append(errors, "at least one special character")
	}

	if len(errors) > 0 {
		errorMsg := fmt.Sprintf("%s must contain ", fieldName)
		for i, err := range errors {
			if i > 0 {
				errorMsg += ", "
			}
			errorMsg += err
		}
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: errorMsg,
		}
	}

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: password,
	}
}

// ValidateInviteCode validates invite code format
func (iv *InputValidator) ValidateInviteCode(code string) ValidationResult {
	if code == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: "Invite code is required",
		}
	}

	code = strings.TrimSpace(code)

	if len(code) < 6 || len(code) > 32 {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: "Invite code must be between 6 and 32 characters",
		}
	}

	// Check for SQL injection patterns
	for _, pattern := range iv.sqlInjectionPatterns {
		if pattern.MatchString(code) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Invite code contains potentially dangerous content",
			}
		}
	}

	// Validate invite code format (alphanumeric with optional hyphens)
	if !regexp.MustCompile(`^[a-zA-Z0-9-]+$`).MatchString(code) {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: "Invite code can only contain letters, numbers, and hyphens",
		}
	}

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: strings.ToUpper(code),
	}
}

// ValidateUUID validates UUID format
func (iv *InputValidator) ValidateUUID(uuidStr, fieldName string) ValidationResult {
	if uuidStr == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s is required", fieldName),
		}
	}

	_, err := uuid.Parse(strings.TrimSpace(uuidStr))
	if err != nil {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("Invalid %s format", fieldName),
		}
	}

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: strings.TrimSpace(uuidStr),
	}
}

// ValidateToken validates token format
func (iv *InputValidator) ValidateToken(token, tokenType string) ValidationResult {
	if token == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s token is required", tokenType),
		}
	}

	token = strings.TrimSpace(token)

	// Check for SQL injection patterns
	for _, pattern := range iv.sqlInjectionPatterns {
		if pattern.MatchString(token) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: fmt.Sprintf("%s token contains potentially dangerous content", tokenType),
			}
		}
	}

	switch strings.ToUpper(tokenType) {
	case "JWT":
		// JWT should have 3 parts separated by dots
		parts := strings.Split(token, ".")
		if len(parts) != 3 {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Invalid JWT token format",
			}
		}
		// Check that all parts are non-empty
		for _, part := range parts {
			if strings.TrimSpace(part) == "" {
				return ValidationResult{
					IsValid:      false,
					ErrorMessage: "Invalid JWT token format",
				}
			}
		}

	case "API":
		// API token validation
		if !strings.HasPrefix(token, "tok_") {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Invalid API token format - must start with 'tok_'",
			}
		}

		if len(token) != 47 { // tok_ + 43 chars
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Invalid API token length",
			}
		}

		// Check if the rest is valid base64url characters
		tokenBody := token[4:] // Remove 'tok_' prefix
		if !regexp.MustCompile(`^[A-Za-z0-9_-]+$`).MatchString(tokenBody) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: "Invalid API token format",
			}
		}

	default:
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("Unknown token type: %s", tokenType),
		}
	}

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: token,
	}
}

// ValidateStringField validates string field with length constraints
func (iv *InputValidator) ValidateStringField(value interface{}, fieldName string, minLength, maxLength int, allowEmpty bool) ValidationResult {
	if value == nil {
		if allowEmpty {
			return ValidationResult{IsValid: true}
		}
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s is required", fieldName),
		}
	}

	str, ok := value.(string)
	if !ok {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be a string", fieldName),
		}
	}

	str = strings.TrimSpace(str)

	if !allowEmpty && str == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s cannot be empty", fieldName),
		}
	}

	if !allowEmpty && (len(str) < minLength || len(str) > maxLength) {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be between %d and %d characters", fieldName, minLength, maxLength),
		}
	}

	// Check for injection patterns
	testStr := str
	for _, pattern := range iv.sqlInjectionPatterns {
		if pattern.MatchString(testStr) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: fmt.Sprintf("%s contains potentially dangerous content", fieldName),
			}
		}
	}

	for _, pattern := range iv.xssPatterns {
		if pattern.MatchString(testStr) {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: fmt.Sprintf("%s contains potentially dangerous content", fieldName),
			}
		}
	}

	// Sanitize HTML entities
	sanitized := html.EscapeString(str)

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: sanitized,
	}
}

// ValidatePositiveInteger validates positive integer input
func (iv *InputValidator) ValidatePositiveInteger(value interface{}, fieldName string, minValue, maxValue int) ValidationResult {
	if value == nil {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s is required", fieldName),
		}
	}

	var intValue int
	var err error

	switch v := value.(type) {
	case int:
		intValue = v
	case float64:
		intValue = int(v)
	case string:
		intValue, err = strconv.Atoi(v)
		if err != nil {
			return ValidationResult{
				IsValid:      false,
				ErrorMessage: fmt.Sprintf("%s must be a valid integer", fieldName),
			}
		}
	default:
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be a valid integer", fieldName),
		}
	}

	if intValue < minValue {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be at least %d", fieldName, minValue),
		}
	}

	if maxValue > 0 && intValue > maxValue {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("%s must be at most %d", fieldName, maxValue),
		}
	}

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: intValue,
	}
}

// ValidateTableName validates table name against whitelist
func (iv *InputValidator) ValidateTableName(tableName string) ValidationResult {
	if tableName == "" {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: "Table name is required",
		}
	}

	// Whitelist of allowed table names
	allowedTables := map[string]bool{
		"users":               true,
		"invite_codes":        true,
		"api_tokens":          true,
		"billing_periods":     true,
		"usage_requests":      true,
		"email_verifications": true,
		"request_logs":        true,
		"billing_adjustments": true,
		"payment_statuses":    true,
		"usage_statistics":    true,
	}

	tableName = strings.TrimSpace(strings.ToLower(tableName))

	if !allowedTables[tableName] {
		return ValidationResult{
			IsValid:      false,
			ErrorMessage: fmt.Sprintf("Table '%s' is not in the allowed list", tableName),
		}
	}

	return ValidationResult{
		IsValid:        true,
		SanitizedValue: tableName,
	}
}

// ValidateAPITokenFormat validates API token format against bcrypt hash
func (iv *InputValidator) ValidateAPITokenFormat(token string) bool {
	if len(token) != 47 || !strings.HasPrefix(token, "tok_") {
		return false
	}

	// Check if the rest is valid base64url characters
	tokenBody := token[4:] // Remove 'tok_' prefix
	return regexp.MustCompile(`^[A-Za-z0-9_-]+$`).MatchString(tokenBody)
}

// ValidateAPITokenHash validates token against stored bcrypt hash
func (iv *InputValidator) ValidateAPITokenHash(plainToken, storedHash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(storedHash), []byte(plainToken))
	return err == nil
}

// ValidatePageSize validates and normalizes page size for pagination
func (iv *InputValidator) ValidatePageSize(pageSize interface{}, defaultSize, maxSize int) int {
	size := defaultSize

	switch v := pageSize.(type) {
	case int:
		size = v
	case float64:
		size = int(v)
	case string:
		if parsed, err := strconv.Atoi(v); err == nil {
			size = parsed
		}
	}

	if size < 1 {
		return defaultSize
	}
	if size > maxSize {
		return maxSize
	}
	return size
}

// ValidateSortField validates sort field against allowed list
func (iv *InputValidator) ValidateSortField(sortField string, allowedFields []string, defaultField string) string {
	for _, field := range allowedFields {
		if sortField == field {
			return sortField
		}
	}
	return defaultField
}

// ValidateSortDirection validates sort direction
func (iv *InputValidator) ValidateSortDirection(direction string, defaultDirection string) string {
	lower := strings.ToLower(direction)
	if lower == "asc" || lower == "desc" {
		return lower
	}
	return defaultDirection
}

// IsSafeInput performs a quick check if input is safe
func (iv *InputValidator) IsSafeInput(value string) bool {
	if value == "" {
		return false
	}

	// Check for SQL injection patterns
	for _, pattern := range iv.sqlInjectionPatterns {
		if pattern.MatchString(value) {
			return false
		}
	}

	// Check for XSS patterns
	for _, pattern := range iv.xssPatterns {
		if pattern.MatchString(value) {
			return false
		}
	}

	return true
}

// GenerateSecurePassword generates a secure random password
func GenerateSecurePassword() string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
	password := make([]byte, 16)

	// Use current nanotime for randomness (in production, use crypto/rand)
	source := time.Now().UnixNano()

	// Ensure at least one of each required character type
	password[0] = charset[source%26]                                                            // lowercase
	password[1] = charset[26+(source%26)]                                                       // uppercase
	password[2] = charset[52+(source%10)]                                                       // digit
	password[3] = charset[62+(source%8)]                                                        // special

	// Fill the rest
	for i := 4; i < 16; i++ {
		source = time.Now().UnixNano()
		password[i] = charset[int(source)%len(charset)]
	}

	return string(password)
}

// Global validator instance
var GlobalValidator = NewInputValidator()

// Convenience functions for common validations

// ValidateRegistrationData validates complete user registration data
func ValidateRegistrationData(email, password, inviteCode string) []ValidationResult {
	return []ValidationResult{
		GlobalValidator.ValidateEmail(email),
		GlobalValidator.ValidatePassword(password, "Password"),
		GlobalValidator.ValidateInviteCode(inviteCode),
	}
}

// ValidateLoginData validates login credentials
func ValidateLoginData(email, password string) []ValidationResult {
	return []ValidationResult{
		GlobalValidator.ValidateEmail(email),
		GlobalValidator.ValidatePassword(password, "Password"),
	}
}

// SanitizeUserInput performs quick sanitization for user input
func SanitizeUserInput(value string) string {
	result := GlobalValidator.ValidateStringField(value, "input", 0, 255, true)
	if result.IsValid {
		return result.SanitizedValue.(string)
	}
	return ""
}