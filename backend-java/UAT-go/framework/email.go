package framework

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"time"
)

// EmailHelper handles email operations via Mailcatcher
type EmailHelper struct {
	mailcatcherURL string
	client         *http.Client
}

// Email represents an email message from Mailcatcher
type Email struct {
	ID         string                 `json:"id"`
	Recipients []string               `json:"recipients"`
	Subject    string                 `json:"subject"`
	From       string                 `json:"from"`
	Headers    map[string]interface{} `json:"headers"`
	CreatedAt  string                 `json:"created_at"`
}

// NewEmailHelper creates a new email helper
func NewEmailHelper(mailcatcherURL string) *EmailHelper {
	return &EmailHelper{
		mailcatcherURL: strings.TrimSuffix(mailcatcherURL, "/"),
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ConnectMailcatcher tests connection to Mailcatcher
func (eh *EmailHelper) ConnectMailcatcher(ctx context.Context) error {
	url := fmt.Sprintf("%s/messages", eh.mailcatcherURL)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := eh.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to connect to Mailcatcher: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Mailcatcher returned status %d", resp.StatusCode)
	}

	return nil
}

// GetLatestEmail gets the latest email for a specific recipient
func (eh *EmailHelper) GetLatestEmail(ctx context.Context, recipientEmail string) (*Email, error) {
	url := fmt.Sprintf("%s/messages", eh.mailcatcherURL)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := eh.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch emails: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to fetch emails, status: %d", resp.StatusCode)
	}

	var emails []Email
	if err := json.NewDecoder(resp.Body).Decode(&emails); err != nil {
		return nil, fmt.Errorf("failed to decode email response: %w", err)
	}

	// Find message to the specified recipient
	for _, email := range emails {
		// Mailcatcher stores recipients as list of strings like ['<email@example.com>']
		// Remove angle brackets for comparison
		for _, recipient := range email.Recipients {
			cleanRecipient := strings.Trim(recipient, "<>")
			if cleanRecipient == recipientEmail {
				return &email, nil
			}
		}
	}

	return nil, fmt.Errorf("no email found for recipient: %s", recipientEmail)
}

// GetEmailContent gets the HTML content of an email
func (eh *EmailHelper) GetEmailContent(ctx context.Context, emailID string) (string, error) {
	url := fmt.Sprintf("%s/messages/%s.html", eh.mailcatcherURL, emailID)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := eh.client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to fetch email content: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("failed to fetch email content, status: %d", resp.StatusCode)
	}

	content := make([]byte, 0)
	buf := make([]byte, 1024)
	for {
		n, err := resp.Body.Read(buf)
		if err != nil && err.Error() != "EOF" {
			return "", fmt.Errorf("failed to read email content: %w", err)
		}
		if n == 0 {
			break
		}
		content = append(content, buf[:n]...)
	}

	return string(content), nil
}

// ExtractVerificationToken extracts verification token from email body
func (eh *EmailHelper) ExtractVerificationToken(emailContent string) (string, error) {
	// Look for verification link pattern
	linkPattern := regexp.MustCompile(`/verify-email\?token=([a-zA-Z0-9._-]+)`)
	matches := linkPattern.FindStringSubmatch(emailContent)
	if len(matches) > 1 {
		return matches[1], nil
	}

	// Look for token parameter pattern
	tokenPattern := regexp.MustCompile(`token=([a-zA-Z0-9._-]+)`)
	matches = tokenPattern.FindStringSubmatch(emailContent)
	if len(matches) > 1 {
		return matches[1], nil
	}

	return "", fmt.Errorf("verification token not found in email")
}

// WaitForEmail waits for an email to arrive with timeout
func (eh *EmailHelper) WaitForEmail(ctx context.Context, recipientEmail string, timeout time.Duration) (*Email, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("timeout waiting for email after %v", timeout)
		case <-ticker.C:
			email, err := eh.GetLatestEmail(ctx, recipientEmail)
			if err == nil && email != nil {
				return email, nil
			}
		}
	}
}

// WaitForEmailWithToken waits for an email and extracts the verification token
func (eh *EmailHelper) WaitForEmailWithToken(ctx context.Context, recipientEmail string, timeout time.Duration) (string, error) {
	email, err := eh.WaitForEmail(ctx, recipientEmail, timeout)
	if err != nil {
		return "", fmt.Errorf("failed to wait for email: %w", err)
	}

	content, err := eh.GetEmailContent(ctx, email.ID)
	if err != nil {
		return "", fmt.Errorf("failed to get email content: %w", err)
	}

	token, err := eh.ExtractVerificationToken(content)
	if err != nil {
		return "", fmt.Errorf("failed to extract verification token: %w", err)
	}

	return token, nil
}

// ClearAllEmails clears all emails in Mailcatcher
func (eh *EmailHelper) ClearAllEmails(ctx context.Context) error {
	url := fmt.Sprintf("%s/messages", eh.mailcatcherURL)
	req, err := http.NewRequestWithContext(ctx, "DELETE", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := eh.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to clear emails: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to clear emails, status: %d", resp.StatusCode)
	}

	return nil
}

// ValidateEmailFormat validates email format
func (eh *EmailHelper) ValidateEmailFormat(email string) bool {
	emailPattern := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	return emailPattern.MatchString(email)
}