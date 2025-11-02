package helpers

import (
	"context"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"

	"uat/config"
	"uat/framework"
)

// AuthenticationError represents authentication-specific errors
type AuthenticationError struct {
	Message string
	Cause   error
}

func (ae *AuthenticationError) Error() string {
	if ae.Cause != nil {
		return fmt.Sprintf("%s: %v", ae.Message, ae.Cause)
	}
	return ae.Message
}

func (ae *AuthenticationError) Unwrap() error {
	return ae.Cause
}

// TokenManager manages JWT and API tokens
type TokenManager struct {
	config         *config.Config
	validator      *InputValidator
	tokenCache     map[string]CachedToken
	secretKey      []byte
}

// CachedToken represents a cached token with expiration
type CachedToken struct {
	Token      string
	ExpiresAt  time.Time
	LastUsed   time.Time
}

// NewTokenManager creates a new token manager
func NewTokenManager(cfg *config.Config) *TokenManager {
	return &TokenManager{
		config:     cfg,
		validator:  NewInputValidator(),
		tokenCache: make(map[string]CachedToken),
		secretKey:  []byte(cfg.JWTIssuer), // In production, use proper secret key management
	}
}

// AuthenticationManager handles authentication operations
type AuthenticationManager struct {
	config    *config.Config
	dbHelper  *framework.DatabaseHelper
	httpClient *framework.HTTPClient
	tokenMgr  *TokenManager
	validator *InputValidator
}

// NewAuthenticationManager creates a new authentication manager
func NewAuthenticationManager(cfg *config.Config, dbHelper *framework.DatabaseHelper, httpClient *framework.HTTPClient) *AuthenticationManager {
	return &AuthenticationManager{
		config:     cfg,
		dbHelper:   dbHelper,
		httpClient: httpClient,
		tokenMgr:   NewTokenManager(cfg),
		validator:  NewInputValidator(),
	}
}

// ExtractJWTToken extracts JWT token from HTTP response
func (am *AuthenticationManager) ExtractJWTToken(resp *framework.HTTPResponse) (string, error) {
	if !resp.IsSuccess() {
		return "", &AuthenticationError{
			Message: fmt.Sprintf("Authentication failed with status %d", resp.Status),
		}
	}

	token, err := resp.ExtractJWTToken()
	if err != nil {
		return "", &AuthenticationError{
			Message: "No token found in response",
			Cause:   err,
		}
	}

	if token == "" {
		return "", &AuthenticationError{
			Message: "Empty token in response",
		}
	}

	return token, nil
}

// ExtractJSONField extracts a field from JSON response
func (am *AuthenticationManager) ExtractJSONField(resp *framework.HTTPResponse, field string) (interface{}, error) {
	return resp.ExtractJSONField(field)
}

// ValidateAPITokenFormat validates API token format
func (am *AuthenticationManager) ValidateAPITokenFormat(token string) bool {
	return am.validator.ValidateAPITokenFormat(token)
}

// AuthenticateUser authenticates a user and returns JWT token
func (am *AuthenticationManager) AuthenticateUser(ctx context.Context, email, password string) (string, error) {
	loginData := map[string]interface{}{
		"email":    email,
		"password": password,
	}

	endpoint, err := am.config.GetEndpoint("login")
	if err != nil {
		return "", &AuthenticationError{
			Message: "Failed to get login endpoint",
			Cause:   err,
		}
	}

	resp, err := am.httpClient.Post(ctx, endpoint, loginData, nil)
	if err != nil {
		return "", &AuthenticationError{
			Message: "Login request failed",
			Cause:   err,
		}
	}

	return am.ExtractJWTToken(resp)
}

// AuthenticateAdmin authenticates admin user and returns JWT token
func (am *AuthenticationManager) AuthenticateAdmin(ctx context.Context) (string, error) {
	if am.config.AdminPassword == "" {
		return "", &AuthenticationError{
			Message: "Admin password not configured",
		}
	}

	return am.AuthenticateUser(ctx, am.config.AdminEmail, am.config.AdminPassword)
}

// CreateUserWithInvite creates a user with invite code and returns registration response
func (am *AuthenticationManager) CreateUserWithInvite(ctx context.Context, email, password, inviteCode string) (*framework.HTTPResponse, error) {
	registrationData := map[string]interface{}{
		"email":             email,
		"password":          password,
		"confirmPassword":   password,
		"inviteCode":        inviteCode,
		"userAcceptedTerms": true,
	}

	endpoint, err := am.config.GetEndpoint("user_register")
	if err != nil {
		return nil, &AuthenticationError{
			Message: "Failed to get registration endpoint",
			Cause:   err,
		}
	}

	resp, err := am.httpClient.Post(ctx, endpoint, registrationData, nil)
	if err != nil {
		return nil, &AuthenticationError{
			Message: "User registration failed",
			Cause:   err,
		}
	}

	return resp, nil
}

// GetAuthenticatedHeaders gets headers with JWT authentication
func (am *AuthenticationManager) GetAuthenticatedHeaders(token string) map[string]string {
	return am.config.GetAuthHeaders(token)
}

// GetAPITokenHeaders gets headers with API token authentication
func (am *AuthenticationManager) GetAPITokenHeaders(apiToken string) map[string]string {
	return am.config.GetAPITokenHeaders(apiToken)
}

// VerifyUserInDatabase checks if user exists in database
func (am *AuthenticationManager) VerifyUserInDatabase(ctx context.Context, email string) (bool, error) {
	return am.dbHelper.VerifyUserExists(ctx, email)
}

// VerifyUserEmailInDatabase directly verifies user email in database for testing
func (am *AuthenticationManager) VerifyUserEmailInDatabase(ctx context.Context, email string) (bool, error) {
	return am.dbHelper.VerifyUserEmailDirectly(ctx, email)
}

// IsJWTTokenExpired checks if JWT token is expired
func (tm *TokenManager) IsJWTTokenExpired(token string) bool {
	parsedToken, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return tm.secretKey, nil
	})

	if err != nil {
		return true // If we can't parse, assume expired
	}

	if claims, ok := parsedToken.Claims.(jwt.MapClaims); ok {
		if exp, ok := claims["exp"].(float64); ok {
			return time.Now().Unix() > int64(exp)
		}
	}

	return true // If no exp claim, assume expired
}

// CacheToken stores a token in cache
func (tm *TokenManager) CacheToken(name, token string) {
	tm.tokenCache[name] = CachedToken{
		Token:     token,
		ExpiresAt: time.Now().Add(24 * time.Hour), // Default 24 hour cache
		LastUsed:  time.Now(),
	}
}

// GetCachedToken retrieves a token from cache
func (tm *TokenManager) GetCachedToken(name string) (string, bool) {
	cached, exists := tm.tokenCache[name]
	if !exists {
		return "", false
	}

	// Check if token is expired
	if time.Now().After(cached.ExpiresAt) {
		delete(tm.tokenCache, name)
		return "", false
	}

	// Update last used time
	cached.LastUsed = time.Now()
	tm.tokenCache[name] = cached

	return cached.Token, true
}

// ClearTokenCache clears token cache for specific user or all users
func (tm *TokenManager) ClearTokenCache(userName string) {
	if userName != "" {
		delete(tm.tokenCache, userName)
	} else {
		tm.tokenCache = make(map[string]CachedToken)
	}
}

// ValidateJWTToken validates JWT token structure and signature
func (tm *TokenManager) ValidateJWTToken(token string) (bool, error) {
	parsedToken, err := jwt.Parse(token, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return tm.secretKey, nil
	})

	if err != nil {
		return false, err
	}

	return parsedToken.Valid, nil
}

// GetAdminToken gets admin JWT token with caching
func (am *AuthenticationManager) GetAdminToken(ctx context.Context, refresh bool) (string, error) {
	cacheKey := "admin"

	if !refresh {
		if token, exists := am.tokenMgr.GetCachedToken(cacheKey); exists {
			// Verify token is not expired
			if !am.tokenMgr.IsJWTTokenExpired(token) {
				return token, nil
			}
		}
	}

	// Get fresh token
	token, err := am.AuthenticateAdmin(ctx)
	if err != nil {
		return "", err
	}

	// Cache the token
	am.tokenMgr.CacheToken(cacheKey, token)

	return token, nil
}

// GetUserToken gets user JWT token with caching
func (am *AuthenticationManager) GetUserToken(ctx context.Context, email, password string, refresh bool) (string, error) {
	cacheKey := fmt.Sprintf("user_%s", email)

	if !refresh {
		if token, exists := am.tokenMgr.GetCachedToken(cacheKey); exists {
			// Verify token is not expired
			if !am.tokenMgr.IsJWTTokenExpired(token) {
				return token, nil
			}
		}
	}

	// Get fresh token
	token, err := am.AuthenticateUser(ctx, email, password)
	if err != nil {
		return "", err
	}

	// Cache the token
	am.tokenMgr.CacheToken(cacheKey, token)

	return token, nil
}

// CreateRegistrationData creates user registration request data
func (am *AuthenticationManager) CreateRegistrationData(email, password, inviteCode string) map[string]interface{} {
	return map[string]interface{}{
		"email":             email,
		"password":          password,
		"confirmPassword":   password,
		"inviteCode":        inviteCode,
		"userAcceptedTerms": true,
	}
}

// CreateLoginData creates login request data
func (am *AuthenticationManager) CreateLoginData(email, password string) map[string]interface{} {
	return map[string]interface{}{
		"email":    email,
		"password": password,
	}
}

// CreatePasswordChangeData creates password change request data
func (am *AuthenticationManager) CreatePasswordChangeData(currentPassword, newPassword string) map[string]interface{} {
	return map[string]interface{}{
		"currentPassword": currentPassword,
		"newPassword":     newPassword,
		"confirmPassword": newPassword,
	}
}

// ValidateEmailFormat validates email format
func (am *AuthenticationManager) ValidateEmailFormat(email string) bool {
	result := am.validator.ValidateEmail(email)
	return result.IsValid
}

// ValidatePasswordStrength validates password strength requirements
func (am *AuthenticationManager) ValidatePasswordStrength(password string) map[string]interface{} {
	result := am.validator.ValidatePassword(password, "Password")

	response := map[string]interface{}{
		"is_valid": result.IsValid,
		"errors":   []string{},
	}

	if !result.IsValid {
		response["errors"] = []string{result.ErrorMessage}
	}

	return response
}

// ValidateInviteCodeFormat validates invite code format
func (am *AuthenticationManager) ValidateInviteCodeFormat(code string) bool {
	result := am.validator.ValidateInviteCode(code)
	return result.IsValid
}

// HashPassword hashes a password using bcrypt
func HashPassword(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", fmt.Errorf("failed to hash password: %w", err)
	}
	return string(hash), nil
}

// CheckPasswordHash checks if a password matches a bcrypt hash
func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// Global instances for convenience
var (
	GlobalAuthManager *AuthenticationManager
	GlobalTokenManager *TokenManager
)

// InitializeGlobalAuth initializes global authentication managers
func InitializeGlobalAuth(cfg *config.Config, dbHelper *framework.DatabaseHelper, httpClient *framework.HTTPClient) {
	GlobalAuthManager = NewAuthenticationManager(cfg, dbHelper, httpClient)
	GlobalTokenManager = NewTokenManager(cfg)
}
