package framework

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// DatabaseHelper handles database operations
type DatabaseHelper struct {
	pool *pgxpool.Pool
}

// NewDatabaseHelper creates a new database helper
func NewDatabaseHelper(databaseURL string) (*DatabaseHelper, error) {
	poolConfig, err := pgxpool.ParseConfig(databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	// Configure connection pool
	poolConfig.MaxConns = 10
	poolConfig.MinConns = 2
	poolConfig.MaxConnLifetime = time.Hour
	poolConfig.HealthCheckPeriod = 5 * time.Minute

	pool, err := pgxpool.NewWithConfig(context.Background(), poolConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create connection pool: %w", err)
	}

	// Test connection
	if err := pool.Ping(context.Background()); err != nil {
		pool.Close()
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	return &DatabaseHelper{
		pool: pool,
	}, nil
}

// Close closes the database connection pool
func (db *DatabaseHelper) Close() error {
	if db.pool != nil {
		db.pool.Close()
	}
	return nil
}

// Ping tests database connectivity
func (db *DatabaseHelper) Ping(ctx context.Context) error {
	return db.pool.Ping(ctx)
}

// ExecuteQuery executes a query and returns the results
func (db *DatabaseHelper) ExecuteQuery(ctx context.Context, query string, args ...interface{}) ([]map[string]interface{}, error) {
	rows, err := db.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("query execution failed: %w", err)
	}
	defer rows.Close()

	var results []map[string]interface{}

	for rows.Next() {
		row, err := rows.Values()
		if err != nil {
			return nil, fmt.Errorf("failed to get row values: %w", err)
		}

		// Get column names
		fieldDescriptions := rows.FieldDescriptions()
		result := make(map[string]interface{})

		for i, col := range fieldDescriptions {
			result[string(col.Name)] = row[i]
		}

		results = append(results, result)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("row iteration error: %w", err)
	}

	return results, nil
}

// ExecuteUpdate executes an INSERT, UPDATE, or DELETE query
func (db *DatabaseHelper) ExecuteUpdate(ctx context.Context, query string, args ...interface{}) (int64, error) {
	commandTag, err := db.pool.Exec(ctx, query, args...)
	if err != nil {
		return 0, fmt.Errorf("update execution failed: %w", err)
	}

	return commandTag.RowsAffected(), nil
}

// VerifyUserExists checks if a user exists in the database
func (db *DatabaseHelper) VerifyUserExists(ctx context.Context, email string) (bool, error) {
	query := "SELECT id FROM users WHERE email = $1"
	results, err := db.ExecuteQuery(ctx, query, email)
	if err != nil {
		return false, err
	}
	return len(results) > 0, nil
}

// VerifyEmailVerified checks if a user's email is verified
func (db *DatabaseHelper) VerifyEmailVerified(ctx context.Context, email string) (bool, error) {
	query := "SELECT id FROM users WHERE email = $1 AND email_verified_at IS NOT NULL"
	results, err := db.ExecuteQuery(ctx, query, email)
	if err != nil {
		return false, err
	}
	return len(results) > 0, nil
}

// VerifyUserEmailDirectly directly verifies a user's email for testing purposes
func (db *DatabaseHelper) VerifyUserEmailDirectly(ctx context.Context, email string) (bool, error) {
	query := "UPDATE users SET email_verified_at = NOW() WHERE email = $1 RETURNING id"
	results, err := db.ExecuteQuery(ctx, query, email)
	if err != nil {
		return false, err
	}
	return len(results) > 0, nil
}

// GetUserID gets a user ID by email
func (db *DatabaseHelper) GetUserID(ctx context.Context, email string) (string, error) {
	query := "SELECT id FROM users WHERE email = $1"
	results, err := db.ExecuteQuery(ctx, query, email)
	if err != nil {
		return "", err
	}
	if len(results) == 0 {
		return "", fmt.Errorf("user not found")
	}
	if id, ok := results[0]["id"].(string); ok {
		return id, nil
	}
	return "", fmt.Errorf("invalid user ID format")
}

// VerifyInviteCodeExists checks if an invite code exists
func (db *DatabaseHelper) VerifyInviteCodeExists(ctx context.Context, code string, activeOnly bool) (bool, error) {
	var query string
	if activeOnly {
		query = "SELECT id FROM invite_codes WHERE code = $1 AND is_active = true"
	} else {
		query = "SELECT id FROM invite_codes WHERE code = $1"
	}
	results, err := db.ExecuteQuery(ctx, query, code)
	if err != nil {
		return false, err
	}
	return len(results) > 0, nil
}

// CheckInviteCodeUsage checks invite code usage status
func (db *DatabaseHelper) CheckInviteCodeUsage(ctx context.Context, code string) (map[string]interface{}, error) {
	query := `
		SELECT ic.code, ic.is_active, ic.used_at, ic.used_by_user_id,
		       u.email as used_by_email
		FROM invite_codes ic
		LEFT JOIN users u ON ic.used_by_user_id = u.id
		WHERE ic.code = $1
	`
	results, err := db.ExecuteQuery(ctx, query, code)
	if err != nil {
		return nil, err
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("invite code not found")
	}
	return results[0], nil
}

// GetUserTokens gets all API tokens for a user
func (db *DatabaseHelper) GetUserTokens(ctx context.Context, userID string) ([]map[string]interface{}, error) {
	query := `
		SELECT id, name, token_prefix, created_at, last_used_at, expires_at, revoked_at
		FROM api_tokens
		WHERE user_id = $1
		ORDER BY created_at DESC
	`
	return db.ExecuteQuery(ctx, query, userID)
}

// GetTokenByID gets an API token by ID
func (db *DatabaseHelper) GetTokenByID(ctx context.Context, tokenID string) (map[string]interface{}, error) {
	query := `
		SELECT id, user_id, name, token_prefix, token_hash, created_at,
		       last_used_at, expires_at, revoked_at
		FROM api_tokens
		WHERE id = $1
	`
	results, err := db.ExecuteQuery(ctx, query, tokenID)
	if err != nil {
		return nil, err
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("token not found")
	}
	return results[0], nil
}

// CheckTokenExists checks if a token exists for a user
func (db *DatabaseHelper) CheckTokenExists(ctx context.Context, userID, name string) (bool, error) {
	query := `
		SELECT id FROM api_tokens
		WHERE user_id = $1 AND name = $2 AND revoked_at IS NULL
	`
	results, err := db.ExecuteQuery(ctx, query, userID, name)
	if err != nil {
		return false, err
	}
	return len(results) > 0, nil
}

// VerifyTokenRevoked checks if a token is revoked
func (db *DatabaseHelper) VerifyTokenRevoked(ctx context.Context, tokenID string) (bool, error) {
	query := `
		SELECT revoked_at FROM api_tokens
		WHERE id = $1 AND revoked_at IS NOT NULL
	`
	results, err := db.ExecuteQuery(ctx, query, tokenID)
	if err != nil {
		return false, err
	}
	return len(results) > 0, nil
}

// GetCurrentBillingPeriod gets the current billing period for a user
func (db *DatabaseHelper) GetCurrentBillingPeriod(ctx context.Context, userID string) (map[string]interface{}, error) {
	query := `
		SELECT id, start_date, end_date, total_requests, total_cost_cents, status
		FROM billing_periods
		WHERE user_id = $1 AND status = 'ACTIVE'
		ORDER BY start_date DESC
		LIMIT 1
	`
	results, err := db.ExecuteQuery(ctx, query, userID)
	if err != nil {
		return nil, err
	}
	if len(results) == 0 {
		return nil, fmt.Errorf("no active billing period found")
	}
	return results[0], nil
}

// GetBillingPeriods gets all billing periods for a user
func (db *DatabaseHelper) GetBillingPeriods(ctx context.Context, userID string) ([]map[string]interface{}, error) {
	query := `
		SELECT id, start_date, end_date, total_requests, total_cost_cents, status
		FROM billing_periods
		WHERE user_id = $1
		ORDER BY start_date DESC
	`
	return db.ExecuteQuery(ctx, query, userID)
}

// WaitForDatabaseUpdate waits for a database update with a timeout
func (db *DatabaseHelper) WaitForDatabaseUpdate(ctx context.Context, table, whereClause string, params []interface{}, timeout time.Duration) (bool, error) {
	// Whitelist of allowed tables to prevent SQL injection
	allowedTables := map[string]bool{
		"users":               true,
		"invite_codes":        true,
		"api_tokens":          true,
		"billing_periods":     true,
		"request_logs":        true,
		"settings":            true,
		"usage_requests":      true,
		"email_verifications": true,
	}

	if !allowedTables[table] {
		return false, fmt.Errorf("table '%s' is not in the allowed list", table)
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	query := fmt.Sprintf("SELECT COUNT(*) as count FROM %s WHERE %s", table, whereClause)

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return false, fmt.Errorf("timeout waiting for database update")
		case <-ticker.C:
			results, err := db.ExecuteQuery(ctx, query, params...)
			if err != nil {
				continue // Retry on error
			}
			if len(results) > 0 {
				if count, ok := results[0]["count"].(int64); ok && count > 0 {
					return true, nil
				}
			}
		}
	}
}
