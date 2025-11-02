package framework

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// HTTPResponse represents an HTTP response with timing information
type HTTPResponse struct {
	Response     *http.Response
	ResponseBody []byte
	ResponseTime time.Duration
	Status       int
}

// HTTPClient handles HTTP operations
type HTTPClient struct {
	baseURL     string
	client      *http.Client
	headers     map[string]string
}

// NewHTTPClient creates a new HTTP client
func NewHTTPClient(baseURL string) *HTTPClient {
	return &HTTPClient{
		baseURL: strings.TrimSuffix(baseURL, "/"),
		client: &http.Client{
			Timeout: 60 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        10,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
			},
		},
		headers: map[string]string{
			"Content-Type": "application/json",
			"Accept":       "application/json",
			"User-Agent":   "TRC-Platform-UAT-Go/1.0.0",
		},
	}
}

// SetTimeout sets the HTTP client timeout
func (hc *HTTPClient) SetTimeout(timeout time.Duration) {
	hc.client.Timeout = timeout
}

// SetDefaultHeaders sets default headers for all requests
func (hc *HTTPClient) SetDefaultHeaders(headers map[string]string) {
	for key, value := range headers {
		hc.headers[key] = value
	}
}

// Post makes a POST request
func (hc *HTTPClient) Post(ctx context.Context, endpoint string, data interface{}, headers map[string]string) (*HTTPResponse, error) {
	return hc.makeRequest(ctx, "POST", endpoint, data, headers)
}

// Get makes a GET request
func (hc *HTTPClient) Get(ctx context.Context, endpoint string, headers map[string]string) (*HTTPResponse, error) {
	return hc.makeRequest(ctx, "GET", endpoint, nil, headers)
}

// Put makes a PUT request
func (hc *HTTPClient) Put(ctx context.Context, endpoint string, data interface{}, headers map[string]string) (*HTTPResponse, error) {
	return hc.makeRequest(ctx, "PUT", endpoint, data, headers)
}

// Delete makes a DELETE request
func (hc *HTTPClient) Delete(ctx context.Context, endpoint string, headers map[string]string) (*HTTPResponse, error) {
	return hc.makeRequest(ctx, "DELETE", endpoint, nil, headers)
}

// makeRequest makes an HTTP request with common logic
func (hc *HTTPClient) makeRequest(ctx context.Context, method, endpoint string, data interface{}, headers map[string]string) (*HTTPResponse, error) {
	// Prepare URL
	url := hc.baseURL + endpoint

	// Prepare request body
	var body io.Reader
	if data != nil {
		jsonData, err := json.Marshal(data)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request data: %w", err)
		}
		body = bytes.NewBuffer(jsonData)
	}

	// Create request
	req, err := http.NewRequestWithContext(ctx, method, url, body)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	for key, value := range hc.headers {
		req.Header.Set(key, value)
	}
	for key, value := range headers {
		req.Header.Set(key, value)
	}

	// Make request with timing
	startTime := time.Now()
	resp, err := hc.client.Do(req)
	responseTime := time.Since(startTime)

	if err != nil {
		return nil, fmt.Errorf("request failed after %v: %w", responseTime, err)
	}
	defer resp.Body.Close()

	// Read response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	return &HTTPResponse{
		Response:     resp,
		ResponseBody: respBody,
		ResponseTime: responseTime,
		Status:       resp.StatusCode,
	}, nil
}

// ExtractJSONField extracts a field from JSON response
func (hr *HTTPResponse) ExtractJSONField(field string) (interface{}, error) {
	var data map[string]interface{}
	if err := json.Unmarshal(hr.ResponseBody, &data); err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON response: %w", err)
	}

	// Handle nested fields (e.g., "data.token")
	fields := strings.Split(field, ".")
	current := data

	for i, f := range fields {
		if i == len(fields)-1 {
			// Last field - return the value
			if value, exists := current[f]; exists {
				return value, nil
			}
			return nil, fmt.Errorf("field '%s' not found in response", field)
		}

		// Navigate to nested object
		if next, exists := current[f]; exists {
			if nextMap, ok := next.(map[string]interface{}); ok {
				current = nextMap
			} else {
				return nil, fmt.Errorf("field '%s' is not an object", strings.Join(fields[:i+1], "."))
			}
		} else {
			return nil, fmt.Errorf("field '%s' not found in response", strings.Join(fields[:i+1], "."))
		}
	}

	return nil, fmt.Errorf("field '%s' not found in response", field)
}

// ExtractJWTToken extracts JWT token from response
func (hr *HTTPResponse) ExtractJWTToken() (string, error) {
	token, err := hr.ExtractJSONField("token")
	if err != nil {
		return "", fmt.Errorf("failed to extract token from response: %w", err)
	}

	if tokenStr, ok := token.(string); ok {
		return tokenStr, nil
	}

	return "", fmt.Errorf("token is not a string")
}

// GetJSONAsMap returns the response body as a map
func (hr *HTTPResponse) GetJSONAsMap() (map[string]interface{}, error) {
	var data map[string]interface{}
	if err := json.Unmarshal(hr.ResponseBody, &data); err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON response: %w", err)
	}
	return data, nil
}

// IsSuccess checks if the response indicates success (2xx status code)
func (hr *HTTPResponse) IsSuccess() bool {
	return hr.Status >= 200 && hr.Status < 300
}

// IsClientError checks if the response indicates a client error (4xx status code)
func (hr *HTTPResponse) IsClientError() bool {
	return hr.Status >= 400 && hr.Status < 500
}

// IsServerError checks if the response indicates a server error (5xx status code)
func (hr *HTTPResponse) IsServerError() bool {
	return hr.Status >= 500
}

// Retryable represents a function that can be retried
type Retryable func() (*HTTPResponse, error)

// RetryWithBackoff executes a function with exponential backoff retry logic
func (hc *HTTPClient) RetryWithBackoff(ctx context.Context, retryable Retryable, maxRetries int, baseDelay time.Duration) (*HTTPResponse, error) {
	var lastErr error

	for attempt := 0; attempt <= maxRetries; attempt++ {
		if attempt > 0 {
			// Calculate delay with exponential backoff
			delay := baseDelay * time.Duration(1<<uint(attempt-1))
			if delay > 30*time.Second {
				delay = 30 * time.Second
			}

			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(delay):
			}
		}

		resp, err := retryable()
		if err == nil {
			return resp, nil
		}

		lastErr = err

		// Don't retry on client errors (4xx)
		if resp != nil && resp.IsClientError() {
			break
		}

		// Don't retry on context cancellation
		if ctx.Err() != nil {
			break
		}
	}

	return nil, fmt.Errorf("request failed after %d attempts: %w", maxRetries+1, lastErr)
}

// ValidateResponse validates response against expected status code
func (hr *HTTPResponse) ValidateResponse(expectedStatus int) error {
	if hr.Status != expectedStatus {
		return fmt.Errorf("expected status %d, got %d. Response body: %s",
			expectedStatus, hr.Status, string(hr.ResponseBody))
	}
	return nil
}

// ValidateSuccessResponse validates response is successful (2xx)
func (hr *HTTPResponse) ValidateSuccessResponse() error {
	if !hr.IsSuccess() {
		return fmt.Errorf("request failed with status %d. Response body: %s",
			hr.Status, string(hr.ResponseBody))
	}
	return nil
}