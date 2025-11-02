# TRC Platform UAT Framework (Go)

A type-safe User Acceptance Test framework for TRC Platform written in Go. This framework provides compile-time safety and better performance compared to the Python version while maintaining all the functionality.

## Features

- **Type Safety**: All configurations, test data, and API responses are strongly typed
- **Compile-time Validation**: Breaking changes trigger compilation errors
- **Performance**: Faster execution for large test suites
- **Concurrency**: Native goroutine support for parallel test execution
- **Comprehensive Error Handling**: Structured error handling with categories and retry logic
- **Input Validation**: Built-in validation for email, password, and other inputs
- **Database Integration**: PostgreSQL support with connection pooling
- **Email Testing**: Mailcatcher integration for email verification testing
- **HTTP Client**: Feature-rich HTTP client with authentication support
- **Test Reporting**: Detailed test execution reports with summaries
- **CLI Interface**: Command-line interface with filtering options

## Architecture

```
UAT-go/
├── main.go                 # Main CLI entry point
├── config/
│   └── config.go          # Configuration management
├── constants/
│   ├── endpoints.go       # API endpoints as global constants
│   └── status_codes.go    # HTTP status codes as global constants
├── framework/
│   ├── database.go        # Database helper with PostgreSQL support
│   ├── httpclient.go      # HTTP client with timing and retry logic
│   ├── email.go           # Email verification via Mailcatcher
│   ├── reporting.go       # Test reporting and summaries
│   ├── types.go           # Core types and interfaces
│   └── colors.go          # Console output formatting
├── helpers/
│   ├── auth.go            # Authentication and token management
│   ├── validation.go      # Input validation and sanitization
│   └── errors.go          # Structured error handling
├── domains/
│   └── test/              # Example test domain
│       ├── test.go        # Test domain implementation
│       └── simple_test.go # Simple test execution
└── go.mod                 # Go module definition
```

## Installation

### Prerequisites

- Go 1.21 or later
- PostgreSQL database
- Mailcatcher (for email testing)
- Access to TRC Platform application

### Setup

1. Clone or navigate to the UAT-go directory:
```bash
cd /Users/therealcisse/Developer/trc_platform/backend-java-21/UAT-go
```

2. Install dependencies:
```bash
go mod tidy
```

3. Build the application:
```bash
go build -o uat-go .
```

## Configuration

The framework uses environment variables for configuration. Required variables:

### Required Environment Variables

- `UAT_ADMIN_PASSWORD` - Admin user password (required)

### Optional Environment Variables

- `UAT_APP_URL` - Application URL (default: http://localhost:8080)
- `UAT_DATABASE_URL` - PostgreSQL connection URL (default: postgresql://trc_user:trc_password@localhost:5432/trc_platform)
- `UAT_MAILCATCHER_URL` - Mailcatcher URL (default: http://localhost:1080)
- `UAT_ADMIN_EMAIL` - Admin email (default: admin@trc-platform.local)
- `UAT_LOG_LEVEL` - Log level (default: INFO)

## Usage

### Basic Commands

```bash
# Show help and available options
./uat-go --help

# Run all tests
./uat-go run

# Run tests with verbose output
./uat-go run --verbose

# Run specific domain
./uat-go run --domain test

# Run specific test by ID
./uat-go run --filter "TEST-01"

# Show test plan without execution
./uat-go run --dry-run

# Run tests matching a pattern
./uat-go run --filter "connectivity"
```

### Command Line Options

- `--domain, -d`: Specify domain to test (test, auth, billing, usage, api_token, image_solve, all)
- `--filter, -f`: Filter tests by ID, name, or description
- `--dry-run, -n`: Show test plan without executing tests
- `--verbose, -v`: Enable verbose output

### Environment Setup

1. Start the TRC Platform application
2. Start PostgreSQL database
3. Start Mailcatcher:
```bash
mailcatcher
```

4. Set required environment variables:
```bash
export UAT_ADMIN_PASSWORD="your-admin-password"
```

5. Run tests:
```bash
./uat-go run
```

## Test Domains

### Test Domain

The framework includes a basic test domain with connectivity and validation tests:

- **TEST-01**: Framework Connectivity Test - Tests database, email, and application connectivity
- **TEST-02**: Input Validation Test - Tests email, password, and invite code validation
- **TEST-03**: Error Handling Test - Tests error creation and logging functionality

### Adding New Domains

To add a new test domain:

1. Create a new package under `domains/`
2. Implement the `framework.Domain` interface:
```go
type YourDomain struct {
    // domain-specific fields
}

func (yd *YourDomain) Name() string { return "your-domain" }
func (yd *YourDomain) Description() string { return "Your domain description" }
func (yd *YourDomain) Setup(ctx context.Context, fw *framework.Framework) error { /* setup logic */ }
func (yd *YourDomain) Cleanup(ctx context.Context, fw *framework.Framework) error { /* cleanup logic */ }
func (yd *YourDomain) GetTests() []framework.Test { /* return tests */ }
```

3. Implement tests that conform to the `framework.Test` interface
4. Register the domain in the main runner

## Type Safety Benefits

### Compile-time Error Detection

```go
// This will cause a compilation error if endpoint name is misspelled
endpoint, err := config.GetEndpoint("logn", true, nil) // Compile error: unknown endpoint

// Fixed version
endpoint, err := config.GetEndpoint("login", true, nil) // OK
```

### Structured Configuration

```go
// All configuration fields are strongly typed
type Config struct {
    AppURL        string        `json:"app_url"`
    HTTPTimeout   time.Duration `json:"http_timeout"`
    AdminEmail    string        `json:"admin_email"`
    // ...
}
```

### Interface-based Architecture

```go
// Database operations use interfaces for testability
type DatabaseHelper interface {
    ExecuteQuery(ctx context.Context, query string, args ...interface{}) ([]map[string]interface{}, error)
    ExecuteUpdate(ctx context.Context, query string, args ...interface{}) (int64, error)
    // ...
}
```

## Error Handling

The framework provides structured error handling with categories and severity levels:

```go
// Create structured error with context
context := helpers.CreateErrorContext("user_login", "authentication", map[string]interface{}{
    "email": "test@example.com",
})

err := helpers.HandleDatabaseError(dbErr, "verify_user", context)
```

Error categories:
- System
- Authentication
- Database
- Network
- Validation
- Configuration
- Test

Error severity levels:
- Low
- Medium
- High
- Critical

## Input Validation

Built-in validation for common input types:

```go
validator := helpers.NewInputValidator()

// Email validation
result := validator.ValidateEmail("test@example.com")
if !result.IsValid {
    fmt.Printf("Error: %s\n", result.ErrorMessage)
}

// Password validation
result := validator.ValidatePassword("TestPass123!", "Password")
if !result.IsValid {
    fmt.Printf("Error: %s\n", result.ErrorMessage)
}

// SQL injection and XSS protection
result := validator.ValidateStringField(userInput, "comment", 1, 1000, false)
```

## Test Results

The framework generates detailed test reports:

```
📊 UAT TEST EXECUTION REPORT
===============================================
📊 Duration: 15.23 seconds
===============================================
📊 Tests Total: 3
✅ Passed: 3
❌ Failed: 0
📈 Success Rate: 100.0%
===============================================

✅ TEST-01: Framework Connectivity Test - PASS
✅ TEST-02: Input Validation Test - PASS
✅ TEST-03: Error Handling Test - PASS
```

## Migration from Python Version

### Key Differences

1. **Static Typing**: All variables and parameters have explicit types
2. **Global Constants**: Endpoints and status codes are compile-time constants
3. **Error Handling**: Uses Go's error handling patterns with structured error types
4. **Concurrency**: Native support for parallel test execution
5. **Compilation**: Breaking changes are caught at compile time

### Equivalent Features

| Python Feature | Go Equivalent |
|---------------|---------------|
| `UATConfig` class | `config.Config` struct |
| `DatabaseHelper` class | `framework.DatabaseHelper` struct |
| `HTTPClient` class | `framework.HTTPClient` struct |
| `TestResult` class | `framework.TestResult` struct |
| Global endpoints dict | `constants` package |
| Exception handling | Structured error types with interfaces |
| Dynamic imports | Static imports with compile-time checking |

## Development

### Running Tests

```bash
# Run the example tests
go run domains/test/simple_test.go

# Run with custom configuration
UAT_ADMIN_PASSWORD="test123" go run main.go run --verbose
```

### Adding Dependencies

```bash
# Add a new dependency
go get github.com/example/package

# Update dependencies
go mod tidy
```

### Building

```bash
# Build for current platform
go build -o uat-go .

# Build for multiple platforms
GOOS=linux go build -o uat-go-linux .
GOOS=windows go build -o uat-go.exe .
```

## Contributing

1. Follow Go coding conventions
2. Add type definitions for new data structures
3. Write tests for new functionality
4. Update documentation
5. Ensure all code compiles without warnings

## License

This framework is part of the TRC Platform project.