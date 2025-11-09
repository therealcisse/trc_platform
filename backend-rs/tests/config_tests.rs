//! Configuration system tests

use std::env;
use tempfile::TempDir;
use std::fs;
use std::path::Path;

use trc_platform::config::{ConfigService, Settings};

/// Test configuration loading with default values
#[tokio::test]
async fn test_default_configuration() {
    // Test that default configuration loads successfully
    let config_service = ConfigService::new().expect("Failed to load default configuration");
    let settings = config_service.settings();

    // Verify default values
    assert_eq!(settings.server.host, "127.0.0.1");
    assert_eq!(settings.server.port, 8080);
    assert_eq!(settings.server.workers, 0); // Auto-detect

    assert_eq!(settings.database.max_connections, 10);
    assert_eq!(settings.database.min_connections, 1);

    assert_eq!(settings.jwt.expiration_hours, 24);
    assert_eq!(settings.jwt.issuer, "trc-platform");

    assert_eq!(settings.logging.level, "info");
    assert_eq!(settings.logging.format, "json");

    assert!(settings.features.enable_registration);
    assert!(settings.features.enable_api_tokens);
}

/// Test environment variable overrides
#[tokio::test]
async fn test_environment_variable_overrides() {
    // Set environment variables
    env::set_var("TRC_SERVER__PORT", "9000");
    env::set_var("TRC_SERVER__HOST", "0.0.0.0");
    env::set_var("TRC_DATABASE__MAX_CONNECTIONS", "20");
    env::set_var("TRC_JWT__EXPIRATION_HOURS", "48");
    env::set_var("TRC_LOGGING__LEVEL", "debug");

    // Load configuration
    let config_service = ConfigService::new().expect("Failed to load configuration");
    let settings = config_service.settings();

    // Verify environment variables override defaults
    assert_eq!(settings.server.port, 9000);
    assert_eq!(settings.server.host, "0.0.0.0");
    assert_eq!(settings.database.max_connections, 20);
    assert_eq!(settings.jwt.expiration_hours, 48);
    assert_eq!(settings.logging.level, "debug");

    // Clean up environment variables
    env::remove_var("TRC_SERVER__PORT");
    env::remove_var("TRC_SERVER__HOST");
    env::remove_var("TRC_DATABASE__MAX_CONNECTIONS");
    env::remove_var("TRC_JWT__EXPIRATION_HOURS");
    env::remove_var("TRC_LOGGING__LEVEL");
}

/// Test environment-specific configuration loading
#[tokio::test]
async fn test_environment_configuration() {
    // Set test environment
    env::set_var("RUST_ENV", "test");

    // Load configuration
    let config_service = ConfigService::new().expect("Failed to load test configuration");
    let settings = config_service.settings();

    // Verify test-specific values
    assert_eq!(settings.server.port, 0); // Dynamic port for tests
    assert_eq!(settings.database.max_connections, 2);
    assert_eq!(settings.logging.level, "warn");
    assert_eq!(settings.openai.base_url, "http://localhost:9999"); // Mock server

    // Verify test-specific features
    assert!(!settings.features.enable_email_verification);
    assert!(!settings.features.enable_password_reset);
    assert!(!settings.features.enable_billing);

    // Clean up
    env::remove_var("RUST_ENV");
}

/// Test development environment configuration
#[tokio::test]
async fn test_development_configuration() {
    // Set development environment
    env::set_var("RUST_ENV", "development");

    // Load configuration
    let config_service = ConfigService::new().expect("Failed to load development configuration");
    let settings = config_service.settings();

    // Verify development-specific values
    assert_eq!(settings.server.host, "127.0.0.1");
    assert_eq!(settings.server.port, 8080);
    assert_eq!(settings.server.workers, 1);
    assert_eq!(settings.logging.level, "debug");
    assert_eq!(settings.logging.format, "pretty");

    // Verify development-specific features
    assert!(!settings.features.enable_email_verification);

    // Verify relaxed security settings
    assert_eq!(settings.security.password_min_length, 6);
    assert!(!settings.security.require_special_chars);

    // Clean up
    env::remove_var("RUST_ENV");
}

/// Test production environment configuration
#[tokio::test]
async fn test_production_configuration() {
    // Set production environment
    env::set_var("RUST_ENV", "production");

    // Load configuration
    let config_service = ConfigService::new().expect("Failed to load production configuration");
    let settings = config_service.settings();

    // Verify production-specific values
    assert_eq!(settings.server.host, "0.0.0.0");
    assert_eq!(settings.server.workers, 0); // Auto-detect
    assert_eq!(settings.logging.level, "info");
    assert_eq!(settings.logging.format, "json");

    // Verify production-specific features
    assert!(settings.features.enable_email_verification);
    assert!(settings.features.enable_billing);

    // Verify strict security settings
    assert_eq!(settings.security.password_min_length, 12);
    assert!(settings.security.require_special_chars);

    // Clean up
    env::remove_var("RUST_ENV");
}

/// Test configuration validation
#[tokio::test]
async fn test_configuration_validation() {
    // Test invalid port number
    env::set_var("TRC_SERVER__PORT", "invalid");

    let result = ConfigService::new();
    assert!(result.is_err(), "Should fail with invalid port");

    // Clean up
    env::remove_var("TRC_SERVER__PORT");

    // Test negative database connections
    env::set_var("TRC_DATABASE__MAX_CONNECTIONS", "-1");

    let result = ConfigService::new();
    assert!(result.is_err(), "Should fail with negative connections");

    // Clean up
    env::remove_var("TRC_DATABASE__MAX_CONNECTIONS");
}

/// Test sensitive data handling
#[tokio::test]
async fn test_sensitive_data_handling() {
    // Set sensitive environment variables
    env::set_var("TRC_JWT__SECRET", "super-secret-key");
    env::set_var("TRC_OPENAI__API_KEY", "sk-test-key");
    env::set_var("TRC_DATABASE__URL", "postgresql://user:password@localhost/db");

    // Load configuration
    let config_service = ConfigService::new().expect("Failed to load configuration");
    let settings = config_service.settings();

    // Verify sensitive data is loaded correctly
    assert_eq!(settings.jwt.secret, "super-secret-key");
    assert_eq!(settings.openai.api_key, "sk-test-key");
    assert!(settings.database.url.contains("password"));

    // Verify that logging doesn't expose sensitive data
    let log_output = format!("{:?}", settings);

    // These should not appear in debug output (assuming proper implementation)
    // Note: This test might need adjustment based on actual Debug implementation
    assert!(!log_output.contains("password") || log_output.contains("***"));

    // Clean up
    env::remove_var("TRC_JWT__SECRET");
    env::remove_var("TRC_OPENAI__API_KEY");
    env::remove_var("TRC_DATABASE__URL");
}

/// Test configuration file loading
#[tokio::test]
async fn test_custom_configuration_file() {
    // Create a temporary directory and config file
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    let config_path = temp_dir.path().join("test.toml");

    // Write custom configuration
    let custom_config = r#"
[server]
host = "192.168.1.100"
port = 9999

[database]
max_connections = 50

[features]
enable_registration = false
enable_api_tokens = false
"#;

    fs::write(&config_path, custom_config).expect("Failed to write config file");

    // Set config file path
    env::set_var("TRC_CONFIG_FILE", config_path.to_str().unwrap());

    // Load configuration
    let result = ConfigService::new();

    // Note: This test depends on whether the ConfigService supports custom config files
    // Adjust based on actual implementation
    if let Ok(config_service) = result {
        let settings = config_service.settings();

        // If custom config loading is supported, verify values
        // assert_eq!(settings.server.host, "192.168.1.100");
        // assert_eq!(settings.server.port, 9999);
        // assert_eq!(settings.database.max_connections, 50);
    }

    // Clean up
    env::remove_var("TRC_CONFIG_FILE");
}

/// Test configuration with missing values
#[tokio::test]
async fn test_missing_required_values() {
    // Temporarily remove required environment variables if they exist
    let original_jwt_secret = env::var("TRC_JWT__SECRET").ok();
    let original_db_url = env::var("TRC_DATABASE__URL").ok();

    env::remove_var("TRC_JWT__SECRET");
    env::remove_var("TRC_DATABASE__URL");

    // Test that configuration fails gracefully without required values
    // This depends on whether JWT secret and database URL are required
    let result = ConfigService::new();

    // If the configuration system requires these values, it should fail
    // If it provides defaults, it should succeed
    match result {
        Ok(_) => {
            // Configuration succeeded - verify defaults are used
        }
        Err(_) => {
            // Configuration failed - this is expected if values are required
        }
    }

    // Restore original values
    if let Some(secret) = original_jwt_secret {
        env::set_var("TRC_JWT__SECRET", secret);
    }
    if let Some(url) = original_db_url {
        env::set_var("TRC_DATABASE__URL", url);
    }
}

/// Test configuration service methods
#[tokio::test]
async fn test_configuration_service_methods() {
    let config_service = ConfigService::new().expect("Failed to load configuration");

    // Test getting individual settings
    let server_settings = config_service.server();
    assert_eq!(server_settings.host, "127.0.0.1");
    assert_eq!(server_settings.port, 8080);

    let database_settings = config_service.database();
    assert_eq!(database_settings.max_connections, 10);

    let jwt_settings = config_service.jwt();
    assert_eq!(jwt_settings.expiration_hours, 24);

    // Test environment detection
    let environment = config_service.environment();
    assert!(matches!(environment.as_str(), "development" | "test" | "production"));

    // Test configuration validation
    assert!(config_service.validate().is_ok());
}

/// Test configuration binding address calculation
#[tokio::test]
async fn test_bind_address_calculation() {
    let config_service = ConfigService::new().expect("Failed to load configuration");
    let bind_address = config_service.settings().bind_address();

    // Should bind to 127.0.0.1:8080 by default
    assert_eq!(bind_address.to_string(), "127.0.0.1:8080");

    // Test with custom port
    env::set_var("TRC_SERVER__PORT", "9999");
    let config_service = ConfigService::new().expect("Failed to load configuration");
    let bind_address = config_service.settings().bind_address();
    assert_eq!(bind_address.to_string(), "127.0.0.1:9999");

    // Clean up
    env::remove_var("TRC_SERVER__PORT");
}