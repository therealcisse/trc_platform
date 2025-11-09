//! Integration tests for the TRC Platform backend

use std::env;
use std::time::Duration;
use tokio::time::timeout;
use reqwest::StatusCode;

/// Test that the application starts successfully with default configuration
#[tokio::test]
async fn test_application_startup_default_config() {
    // Set test environment to avoid interfering with other tests
    env::set_var("RUST_ENV", "test");

    // Set a different port to avoid conflicts
    env::set_var("TRC_SERVER__PORT", "0"); // Use dynamic port

    // Note: This test would require the application to be running
    // In a real scenario, you might use:
    // 1. Testcontainers to spin up required services
    // 2. Process spawning to start the application
    // 3. HTTP client to test endpoints

    // For now, we'll test configuration loading which we can do without starting the server
    let config_service = trc_platform::config::ConfigService::new()
        .expect("Failed to load configuration");

    // Verify configuration loads correctly
    assert!(config_service.validate().is_ok());

    // Clean up
    env::remove_var("RUST_ENV");
    env::remove_var("TRC_SERVER__PORT");
}

/// Test configuration loading in different environments
#[tokio::test]
async fn test_configuration_environments() {
    let environments = vec!["development", "test", "production"];

    for env in environments {
        // Set environment
        env::set_var("RUST_ENV", env);

        // Load configuration
        let config_service = trc_platform::config::ConfigService::new()
            .expect(&format!("Failed to load {} configuration", env));

        // Verify configuration is valid
        assert!(config_service.validate().is_ok(),
               "Configuration validation failed for environment: {}", env);

        // Verify environment-specific settings
        let settings = config_service.settings();

        match env {
            "development" => {
                assert_eq!(settings.logging.level, "debug");
                assert_eq!(settings.logging.format, "pretty");
                assert_eq!(settings.server.workers, 1);
            }
            "test" => {
                assert_eq!(settings.logging.level, "warn");
                assert_eq!(settings.server.port, 0); // Dynamic port
                assert!(!settings.features.enable_email_verification);
            }
            "production" => {
                assert_eq!(settings.logging.level, "info");
                assert_eq!(settings.logging.format, "json");
                assert_eq!(settings.server.host, "0.0.0.0");
                assert_eq!(settings.security.password_min_length, 12);
            }
            _ => {}
        }
    }

    // Clean up
    env::remove_var("RUST_ENV");
}

/// Test that environment variables properly override configuration files
#[tokio::test]
async fn test_environment_variable_override() {
    // Set test environment
    env::set_var("RUST_ENV", "test");

    // Set environment variables
    env::set_var("TRC_SERVER__PORT", "12345");
    env::set_var("TRC_LOGGING__LEVEL", "trace");
    env::set_var("TRC_DATABASE__MAX_CONNECTIONS", "99");

    // Load configuration
    let config_service = trc_platform::config::ConfigService::new()
        .expect("Failed to load configuration");

    let settings = config_service.settings();

    // Verify environment variables override file configuration
    assert_eq!(settings.server.port, 12345);
    assert_eq!(settings.logging.level, "trace");
    assert_eq!(settings.database.max_connections, 99);

    // Clean up
    env::remove_var("RUST_ENV");
    env::remove_var("TRC_SERVER__PORT");
    env::remove_var("TRC_LOGGING__LEVEL");
    env::remove_var("TRC_DATABASE__MAX_CONNECTIONS");
}

/// Test configuration validation with various scenarios
#[tokio::test]
async fn test_configuration_validation_scenarios() {
    // Test 1: Valid configuration should pass
    env::set_var("RUST_ENV", "development");
    let config_service = trc_platform::config::ConfigService::new()
        .expect("Failed to load configuration");
    assert!(config_service.validate().is_ok());

    // Test 2: Invalid port should fail
    env::set_var("TRC_SERVER__PORT", "invalid_port");
    let result = trc_platform::config::ConfigService::new();
    assert!(result.is_err(), "Should fail with invalid port");
    env::remove_var("TRC_SERVER__PORT");

    // Test 3: Negative database connections should fail
    env::set_var("TRC_DATABASE__MAX_CONNECTIONS", "-5");
    let result = trc_platform::config::ConfigService::new();
    assert!(result.is_err(), "Should fail with negative connections");
    env::remove_var("TRC_DATABASE__MAX_CONNECTIONS");

    // Test 4: Invalid log level should fail
    env::set_var("TRC_LOGGING__LEVEL", "invalid_level");
    let result = trc_platform::config::ConfigService::new();
    assert!(result.is_err(), "Should fail with invalid log level");
    env::remove_var("TRC_LOGGING__LEVEL");

    // Clean up
    env::remove_var("RUST_ENV");
}

/// Test configuration service methods
#[tokio::test]
async fn test_configuration_service_api() {
    env::set_var("RUST_ENV", "test");

    let config_service = trc_platform::config::ConfigService::new()
        .expect("Failed to load configuration");

    // Test individual section accessors
    let server = config_service.server();
    assert_eq!(server.port, 0); // Test environment default

    let database = config_service.database();
    assert_eq!(database.max_connections, 2); // Test environment default

    let jwt = config_service.jwt();
    assert_eq!(jwt.expiration_hours, 1); // Test environment default

    let features = config_service.features();
    assert!(!features.enable_email_verification); // Test environment default

    let security = config_service.security();
    assert_eq!(security.password_min_length, 4); // Test environment default

    // Test environment detection
    let environment = config_service.environment();
    assert_eq!(environment, "test");

    // Test settings access
    let settings = config_service.settings();
    assert!(settings.bind_address().port() > 0);

    // Clean up
    env::remove_var("RUST_ENV");
}

/// Test that configuration files exist and are accessible
#[tokio::test]
async fn test_configuration_files_exist() {
    use std::path::Path;

    let config_files = vec![
        "config/default.toml",
        "config/development.toml",
        "config/test.toml",
        "config/production.toml",
        "config/local.toml.example",
    ];

    for file in config_files {
        let path = Path::new(file);
        assert!(path.exists(), "Configuration file should exist: {}", file);

        // Verify file is readable
        let content = std::fs::read_to_string(path)
            .expect(&format!("Should be able to read configuration file: {}", file));

        assert!(!content.is_empty(), "Configuration file should not be empty: {}", file);

        // Verify it's valid TOML (basic check)
        assert!(content.contains('[') || content.is_empty(),
               "Configuration file should contain TOML sections: {}", file);
    }
}

/// Test documentation file exists
#[tokio::test]
async fn test_documentation_exists() {
    use std::path::Path;

    let doc_file = Path::new("docs/configuration.md");
    assert!(doc_file.exists(), "Configuration documentation should exist");

    let content = std::fs::read_to_string(doc_file)
        .expect("Should be able to read configuration documentation");

    // Verify documentation contains key sections
    assert!(content.contains("# Configuration Management Guide"));
    assert!(content.contains("## Environment Variables"));
    assert!(content.contains("## Configuration Reference"));
    assert!(content.contains("## Security Considerations"));
}

/// Test that the application can handle different configuration scenarios
#[tokio::test]
async fn test_configuration_resilience() {
    // Test 1: Missing environment variables should use defaults
    env::set_var("RUST_ENV", "development");

    // Remove potentially conflicting environment variables
    env::remove_var("TRC_SERVER__PORT");
    env::remove_var("TRC_DATABASE__URL");
    env::remove_var("TRC_JWT__SECRET");

    let config_service = trc_platform::config::ConfigService::new()
        .expect("Failed to load configuration with minimal environment");

    // Should use defaults from configuration files
    let settings = config_service.settings();
    assert_eq!(settings.server.port, 8080); // Default from development.toml

    // Test 2: Empty environment variables should be handled gracefully
    env::set_var("TRC_SERVER__HOST", ""); // Empty value

    let config_service = trc_platform::config::ConfigService::new()
        .expect("Should handle empty environment variables");

    // Should fall back to file configuration
    let settings = config_service.settings();
    assert_eq!(settings.server.host, "127.0.0.1"); // From development.toml

    // Clean up
    env::remove_var("RUST_ENV");
    env::remove_var("TRC_SERVER__HOST");
}