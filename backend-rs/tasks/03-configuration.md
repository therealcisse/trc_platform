# Task 3: Configuration Management

## Description
Implement comprehensive configuration management using Figment for type-safe, hierarchical configuration. This task handles environment variables, config files, and provides a centralized configuration system with validation and hot-reload capabilities.

## Acceptance Criteria
1. ✅ Implement Figment-based configuration with multiple sources (env, toml, json)
2. ✅ Create type-safe configuration structs with validation
3. ✅ Set up environment-specific configurations (dev, test, prod)
4. ✅ Implement configuration loading with proper error handling
5. ✅ Add configuration validation and default values
6. ✅ Create configuration examples and documentation
7. ✅ Test configuration loading in different environments

## Prerequisites
- **Task 1**: Project Setup (completed)
- **Task 2**: Database Schema (completed - for database config validation)

## Technical Implementation

### Step 1: Enhanced Configuration Structs

#### Update src/config/settings.rs
```rust
//! Application settings and configuration management with Figment

use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use figment::{Figment, providers::{Env, Toml, Json, Format}};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub server: ServerSettings,
    pub database: DatabaseSettings,
    pub openai: OpenAISettings,
    pub jwt: JwtSettings,
    pub email: EmailSettings,
    pub cache: CacheSettings,
    pub logging: LoggingSettings,
    pub cors: CorsSettings,
    pub environment: Environment,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerSettings {
    pub host: String,
    pub port: u16,
    pub workers: Option<usize>,
    pub keep_alive: Option<u64>,
    pub request_timeout_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseSettings {
    pub url: String,
    pub max_connections: u32,
    pub min_connections: u32,
    pub acquire_timeout_seconds: u64,
    pub idle_timeout_seconds: u64,
    pub max_lifetime_seconds: u64,
    pub connect_timeout_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenAISettings {
    pub api_key: String,
    pub model: String,
    pub timeout_seconds: u64,
    pub max_retries: u32,
    pub base_url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JwtSettings {
    pub secret: String,
    pub ttl_hours: u64,
    pub refresh_ttl_days: Option<u64>,
    pub issuer: Option<String>,
    pub audience: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailSettings {
    pub smtp_host: String,
    pub smtp_port: u16,
    pub smtp_username: String,
    pub smtp_password: String,
    pub from_address: String,
    pub from_name: String,
    pub use_tls: bool,
    pub connection_timeout_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheSettings {
    pub redis_url: Option<String>,
    pub ttl_seconds: u64,
    pub max_capacity: Option<usize>,
    pub local_cache_size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingSettings {
    pub level: String,
    pub format: String, // "json" or "pretty"
    pub include_spans: bool,
    pub include_target: bool,
    pub otlp_endpoint: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorsSettings {
    pub allowed_origins: Vec<String>,
    pub allowed_methods: Vec<String>,
    pub allowed_headers: Vec<String>,
    pub expose_headers: Vec<String>,
    pub max_age: Option<u64>,
    pub allow_credentials: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Environment {
    Development,
    Test,
    Staging,
    Production,
}

impl Default for Environment {
    fn default() -> Self {
        Environment::Development
    }
}

impl Settings {
    /// Load configuration from multiple sources
    pub fn load() -> Result<Self, figment::Error> {
        let base_config = Figment::new()
            // Base defaults
            .merge(Toml::file("config/default.toml"))
            // Environment-specific overrides
            .merge(Toml::file(format!("config/{}.toml", Environment::default().as_str())).nested())
            // Local development overrides
            .merge(Toml::file("config/local.toml").nested())
            // Environment variable overrides
            .merge(Env::prefixed("TRC_").split("__"))
            // Command-line arguments (if provided)
            .merge(Json::file("config/override.json").nested());

        base_config.extract()
    }

    /// Load configuration with custom environment
    pub fn load_with_env(env: Environment) -> Result<Self, figment::Error> {
        let base_config = Figment::new()
            // Base defaults
            .merge(Toml::file("config/default.toml"))
            // Environment-specific overrides
            .merge(Toml::file(format!("config/{}.toml", env.as_str())).nested())
            // Environment variable overrides
            .merge(Env::prefixed("TRC_").split("__"));

        base_config.extract()
    }

    /// Validate configuration
    pub fn validate(&self) -> Result<(), String> {
        // Validate server settings
        if self.server.port == 0 || self.server.port > 65535 {
            return Err("Invalid server port".to_string());
        }

        // Validate database URL
        if !self.database.url.starts_with("postgresql://") {
            return Err("Database URL must start with postgresql://".to_string());
        }

        // Validate JWT secret (must be at least 32 characters for HS256)
        if self.jwt.secret.len() < 32 {
            return Err("JWT secret must be at least 32 characters".to_string());
        }

        // Validate OpenAI settings
        if self.openai.api_key.is_empty() {
            return Err("OpenAI API key is required".to_string());
        }

        // Validate email settings
        if self.email.smtp_host.is_empty() || self.email.smtp_port == 0 {
            return Err("Valid SMTP settings are required".to_string());
        }

        Ok(())
    }

    /// Get server bind address
    pub fn bind_address(&self) -> SocketAddr {
        format!("{}:{}", self.server.host, self.server.port)
            .parse()
            .expect("Invalid server bind address")
    }

    /// Get environment as string
    pub fn environment_name(&self) -> &'static str {
        self.environment.as_str()
    }

    /// Check if running in development
    pub fn is_development(&self) -> bool {
        matches!(self.environment, Environment::Development)
    }

    /// Check if running in production
    pub fn is_production(&self) -> bool {
        matches!(self.environment, Environment::Production)
    }
}

impl Environment {
    pub fn as_str(&self) -> &'static str {
        match self {
            Environment::Development => "development",
            Environment::Test => "test",
            Environment::Staging => "staging",
            Environment::Production => "production",
        }
    }

    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "development" | "dev" => Environment::Development,
            "test" => Environment::Test,
            "staging" | "stage" => Environment::Staging,
            "production" | "prod" => Environment::Production,
            _ => Environment::Development,
        }
    }
}

impl Default for ServerSettings {
    fn default() -> Self {
        Self {
            host: "127.0.0.1".to_string(),
            port: 8080,
            workers: None,
            keep_alive: Some(30),
            request_timeout_ms: 30000,
        }
    }
}

impl Default for DatabaseSettings {
    fn default() -> Self {
        Self {
            url: "postgresql://trc_user:trc_password@localhost:5432/trc_platform".to_string(),
            max_connections: 20,
            min_connections: 5,
            acquire_timeout_seconds: 10,
            idle_timeout_seconds: 300,
            max_lifetime_seconds: 600,
            connect_timeout_ms: 10000,
        }
    }
}

impl Default for OpenAISettings {
    fn default() -> Self {
        Self {
            api_key: "".to_string(),
            model: "gpt-4.1-mini-2025-04-14".to_string(),
            timeout_seconds: 30,
            max_retries: 3,
            base_url: "https://api.openai.com/v1/chat/completions".to_string(),
        }
    }
}

impl Default for JwtSettings {
    fn default() -> Self {
        Self {
            secret: "change-this-super-secret-key-in-production".to_string(),
            ttl_hours: 24,
            refresh_ttl_days: Some(7),
            issuer: Some("trc-platform".to_string()),
            audience: Some("trc-platform-users".to_string()),
        }
    }
}

impl Default for EmailSettings {
    fn default() -> Self {
        Self {
            smtp_host: "localhost".to_string(),
            smtp_port: 587,
            smtp_username: "".to_string(),
            smtp_password: "".to_string(),
            from_address: "noreply@trcplatform.com".to_string(),
            from_name: "TRC Platform".to_string(),
            use_tls: true,
            connection_timeout_ms: 5000,
        }
    }
}

impl Default for CacheSettings {
    fn default() -> Self {
        Self {
            redis_url: None,
            ttl_seconds: 3600,
            max_capacity: Some(10000),
            local_cache_size: 1000,
        }
    }
}

impl Default for LoggingSettings {
    fn default() -> Self {
        Self {
            level: "info".to_string(),
            format: "pretty".to_string(),
            include_spans: true,
            include_target: true,
            otlp_endpoint: None,
        }
    }
}

impl Default for CorsSettings {
    fn default() -> Self {
        Self {
            allowed_origins: vec!["http://localhost:3000".to_string()],
            allowed_methods: vec!["GET".to_string(), "POST".to_string(), "PUT".to_string(), "DELETE".to_string()],
            allowed_headers: vec!["*".to_string()],
            expose_headers: vec![],
            max_age: Some(3600),
            allow_credentials: true,
        }
    }
}
```

### Step 2: Create Configuration Files

#### config/default.toml
```toml
[server]
host = "127.0.0.1"
port = 8080
workers = null
keep_alive = 30
request_timeout_ms = 30000

[database]
url = "postgresql://trc_user:trc_password@localhost:5432/trc_platform"
max_connections = 20
min_connections = 5
acquire_timeout_seconds = 10
idle_timeout_seconds = 300
max_lifetime_seconds = 600
connect_timeout_ms = 10000

[openai]
api_key = ""
model = "gpt-4.1-mini-2025-04-14"
timeout_seconds = 30
max_retries = 3
base_url = "https://api.openai.com/v1/chat/completions"

[jwt]
secret = "change-this-super-secret-key-in-production"
ttl_hours = 24
refresh_ttl_days = 7
issuer = "trc-platform"
audience = "trc-platform-users"

[email]
smtp_host = "localhost"
smtp_port = 587
smtp_username = ""
smtp_password = ""
from_address = "noreply@trcplatform.com"
from_name = "TRC Platform"
use_tls = true
connection_timeout_ms = 5000

[cache]
redis_url = null
ttl_seconds = 3600
max_capacity = 10000
local_cache_size = 1000

[logging]
level = "info"
format = "pretty"
include_spans = true
include_target = true
otlp_endpoint = null

[cors]
allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
allowed_headers = ["*"]
expose_headers = []
max_age = 3600
allow_credentials = true

[environment]
# This will be overridden by environment-specific config files
```

#### config/development.toml
```toml
[server]
host = "127.0.0.1"
port = 8080

[database]
url = "postgresql://trc_user:trc_password@localhost:5432/trc_platform_dev"

[logging]
level = "debug"
format = "pretty"

[cors]
allowed_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"]

[environment]
# Development environment specific settings
```

#### config/test.toml
```toml
[server]
port = 0 # Random port for tests

[database]
url = "postgresql://trc_user:trc_password@localhost:5432/trc_platform_test"
max_connections = 5
min_connections = 1

[openai]
api_key = "test-key"
base_url = "http://localhost:8081/mock-openai"

[email]
smtp_host = "localhost"
smtp_port = 1025
from_address = "test@trcplatform.com"

[cache]
redis_url = null # Use local cache only in tests
local_cache_size = 100

[logging]
level = "warn"
format = "json"

[cors]
allowed_origins = ["*"]

[environment]
# Test environment specific settings
```

#### config/production.toml
```toml
[server]
workers = null # Let the OS decide
keep_alive = 60
request_timeout_ms = 60000

[database]
max_connections = 50
min_connections = 10
acquire_timeout_seconds = 5

[openai]
timeout_seconds = 60
max_retries = 5

[jwt]
ttl_hours = 8 # Shorter session in production

[email]
use_tls = true
connection_timeout_ms = 10000

[cache]
redis_url = "${TRC_REDIS_URL}"
ttl_seconds = 1800 # 30 minutes
max_capacity = 100000
local_cache_size = 5000

[logging]
level = "info"
format = "json"
include_spans = false
otlp_endpoint = "${TRC_OTLP_ENDPOINT}"

[cors]
allowed_origins = [] # Must be set via environment
allow_credentials = true

[environment]
# Production environment specific settings
```

#### config/local.toml.example
```toml
# This file should not be committed to version control
# Copy to config/local.toml and customize for local development

[server]
port = 8081

[database]
url = "postgresql://localuser:localpass@localhost:5432/trc_platform_local"

[openai]
api_key = "your-openai-api-key-here"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your-email@gmail.com"
smtp_password = "your-app-password"

[cache]
redis_url = "redis://localhost:6379"

[logging]
level = "trace"
```

### Step 3: Configuration Service

#### src/config/service.rs
```rust
//! Configuration service with validation and hot-reload capabilities

use std::sync::Arc;
use tokio::sync::RwLock;
use crate::config::Settings;
use crate::AppError;

pub type ConfigRef = Arc<RwLock<Settings>>;

/// Configuration service providing type-safe access to settings
#[derive(Clone)]
pub struct ConfigService {
    settings: ConfigRef,
}

impl ConfigService {
    /// Create new configuration service
    pub async fn new() -> Result<Self, AppError> {
        let settings = Settings::load()
            .map_err(|e| AppError::Config(format!("Failed to load configuration: {}", e)))?;

        // Validate configuration
        settings.validate()
            .map_err(|e| AppError::Config(format!("Configuration validation failed: {}", e)))?;

        let service = Self {
            settings: Arc::new(RwLock::new(settings)),
        };

        // Log configuration (without sensitive data)
        service.log_configuration().await;

        Ok(service)
    }

    /// Create configuration service for specific environment
    pub async fn with_environment(env: crate::config::Environment) -> Result<Self, AppError> {
        let settings = Settings::load_with_env(env)
            .map_err(|e| AppError::Config(format!("Failed to load configuration for {:?}: {}", env, e)))?;

        settings.validate()
            .map_err(|e| AppError::Config(format!("Configuration validation failed: {}", e)))?;

        let service = Self {
            settings: Arc::new(RwLock::new(settings)),
        };

        service.log_configuration().await;
        Ok(service)
    }

    /// Get current settings
    pub async fn get(&self) -> Settings {
        self.settings.read().await.clone()
    }

    /// Get database settings
    pub async fn database(&self) -> crate::config::DatabaseSettings {
        self.settings.read().await.database.clone()
    }

    /// Get server settings
    pub async fn server(&self) -> crate::config::ServerSettings {
        self.settings.read().await.server.clone()
    }

    /// Get OpenAI settings
    pub async fn openai(&self) -> crate::config::OpenAISettings {
        self.settings.read().await.openai.clone()
    }

    /// Get JWT settings
    pub async fn jwt(&self) -> crate::config::JwtSettings {
        self.settings.read().await.jwt.clone()
    }

    /// Get email settings
    pub async fn email(&self) -> crate::config::EmailSettings {
        self.settings.read().await.email.clone()
    }

    /// Get cache settings
    pub async fn cache(&self) -> crate::config::CacheSettings {
        self.settings.read().await.cache.clone()
    }

    /// Get logging settings
    pub async fn logging(&self) -> crate::config::LoggingSettings {
        self.settings.read().await.logging.clone()
    }

    /// Get CORS settings
    pub async fn cors(&self) -> crate::config::CorsSettings {
        self.settings.read().await.cors.clone()
    }

    /// Check if running in development
    pub async fn is_development(&self) -> bool {
        self.settings.read().await.is_development()
    }

    /// Check if running in production
    pub async fn is_production(&self) -> bool {
        self.settings.read().await.is_production()
    }

    /// Get environment name
    pub async fn environment(&self) -> &'static str {
        self.settings.read().await.environment_name()
    }

    /// Log configuration (without sensitive data)
    async fn log_configuration(&self) {
        let settings = self.settings.read().await;

        tracing::info!("Configuration loaded successfully");
        tracing::info!("Environment: {:?}", settings.environment);
        tracing::info!("Server: {}:{}", settings.server.host, settings.server.port);
        tracing::info!("Database: {} (max_connections: {})",
            settings.database.url.split('@').last().unwrap_or("unknown"),
            settings.database.max_connections
        );
        tracing::info!("OpenAI Model: {}", settings.openai.model);
        tracing::info!("JWT TTL: {} hours", settings.jwt.ttl_hours);
        tracing::info!("Cache: Redis={}, TTL={}s",
            settings.cache.redis_url.is_some(),
            settings.cache.ttl_seconds
        );
        tracing::info!("Logging Level: {}", settings.logging.level);

        // Don't log sensitive data like passwords, API keys, etc.
    }

    /// Update configuration (for hot-reload in development)
    #[cfg(debug_assertions)]
    pub async fn reload(&self) -> Result<(), AppError> {
        let new_settings = Settings::load()
            .map_err(|e| AppError::Config(format!("Failed to reload configuration: {}", e)))?;

        new_settings.validate()
            .map_err(|e| AppError::Config(format!("Configuration validation failed: {}", e)))?;

        let mut settings = self.settings.write().await;
        *settings = new_settings;

        tracing::info!("Configuration reloaded successfully");
        Ok(())
    }

    /// Get configuration as JSON (for debugging)
    pub async fn as_json(&self) -> Result<String, AppError> {
        let settings = self.settings.read().await;
        serde_json::to_string_pretty(&settings)
            .map_err(|e| AppError::Config(format!("Failed to serialize configuration: {}", e)))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;

    #[tokio::test]
    async fn test_config_loading() {
        // Set test environment variables
        env::set_var("TRC_ENVIRONMENT", "test");
        env::set_var("TRC_DATABASE__URL", "postgresql://test:test@localhost:5432/test");

        let config_service = ConfigService::new().await;
        assert!(config_service.is_ok());

        if let Ok(service) = config_service {
            let settings = service.get().await;
            assert_eq!(settings.server.port, 0); // From test config
        }
    }

    #[tokio::test]
    async fn test_config_validation() {
        let mut settings = Settings::default();

        // Test invalid port
        settings.server.port = 70000;
        assert!(settings.validate().is_err());

        // Test invalid JWT secret
        settings.server.port = 8080;
        settings.jwt.secret = "short".to_string();
        assert!(settings.validate().is_err());

        // Test valid configuration
        settings.jwt.secret = "this-is-a-valid-secret-key-that-is-long-enough".to_string();
        settings.openai.api_key = "test-key".to_string();
        assert!(settings.validate().is_ok());
    }
}
```

### Step 4: Update Configuration Module

#### Update src/config/mod.rs
```rust
//! Configuration management module

pub mod settings;
pub mod service;

pub use settings::*;
pub use service::*;
```

### Step 5: Environment Variable Documentation

#### docs/configuration.md
```markdown
# Configuration Guide

## Environment Variables

All environment variables should be prefixed with `TRC_` and use double underscores (`__`) for nested configuration.

### Server Configuration
- `TRC_SERVER__HOST` - Server host (default: 127.0.0.1)
- `TRC_SERVER__PORT` - Server port (default: 8080)
- `TRC_SERVER__WORKERS` - Number of worker threads
- `TRC_SERVER__REQUEST_TIMEOUT_MS` - Request timeout in milliseconds

### Database Configuration
- `TRC_DATABASE__URL` - PostgreSQL connection URL
- `TRC_DATABASE__MAX_CONNECTIONS` - Maximum database connections (default: 20)
- `TRC_DATABASE__MIN_CONNECTIONS` - Minimum database connections (default: 5)
- `TRC_DATABASE__ACQUIRE_TIMEOUT_SECONDS` - Connection acquisition timeout
- `TRC_DATABASE__IDLE_TIMEOUT_SECONDS` - Connection idle timeout

### OpenAI Configuration
- `TRC_OPENAI__API_KEY` - OpenAI API key (required)
- `TRC_OPENAI__MODEL` - OpenAI model name (default: gpt-4.1-mini-2025-04-14)
- `TRC_OPENAI__TIMEOUT_SECONDS` - Request timeout in seconds

### JWT Configuration
- `TRC_JWT__SECRET` - JWT signing secret (minimum 32 characters)
- `TRC_JWT__TTL_HOURS` - Token time-to-live in hours (default: 24)

### Email Configuration
- `TRC_EMAIL__SMTP_HOST` - SMTP server hostname
- `TRC_EMAIL__SMTP_PORT` - SMTP server port
- `TRC_EMAIL__SMTP_USERNAME` - SMTP username
- `TRC_EMAIL__SMTP_PASSWORD` - SMTP password
- `TRC_EMAIL__FROM_ADDRESS` - From email address

### Cache Configuration
- `TRC_CACHE__REDIS_URL` - Redis connection URL (optional)
- `TRC_CACHE__TTL_SECONDS` - Cache TTL in seconds (default: 3600)

### Logging Configuration
- `TRC_LOGGING__LEVEL` - Log level (trace, debug, info, warn, error)
- `TRC_LOGGING__FORMAT` - Log format (pretty, json)

### CORS Configuration
- `TRC_CORS__ALLOWED_ORIGINS` - Comma-separated list of allowed origins

## Configuration Files

### Priority Order
1. Environment variables (highest priority)
2. `config/override.json`
3. `config/local.toml`
4. `config/{environment}.toml`
5. `config/default.toml` (lowest priority)

### Environment-Specific Files
- `config/development.toml` - Development environment
- `config/test.toml` - Test environment
- `config/staging.toml` - Staging environment
- `config/production.toml` - Production environment

## Examples

### Development Setup
```bash
export TRC_OPENAI__API_KEY="your-openai-api-key"
export TRC_JWT__SECRET="your-256-bit-secret-key"
export TRC_EMAIL__SMTP_PASSWORD="your-smtp-password"
```

### Production Setup
```bash
export TRC_ENVIRONMENT="production"
export TRC_DATABASE__URL="postgresql://user:pass@prod-db:5432/trc_platform"
export TRC_OPENAI__API_KEY="${OPENAI_API_KEY}"
export TRC_JWT__SECRET="${JWT_SECRET}"
export TRC_REDIS_URL="redis://redis:6379"
export TRC_LOGGING__FORMAT="json"
export TRC_CORS__ALLOWED_ORIGINS="https://app.trcplatform.com"
```
```

### Step 6: Update Main Application

#### Update src/main.rs
```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use trc_platform::config::{ConfigService, Environment};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load configuration
    let config_service = ConfigService::new().await?;

    // Initialize tracing based on configuration
    let logging_config = config_service.logging().await;

    let subscriber = tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| logging_config.level.clone()),
        )
        .with(match logging_config.format.as_str() {
            "json" => tracing_subscriber::fmt::layer().json().boxed(),
            _ => tracing_subscriber::fmt::layer().boxed(),
        });

    subscriber.init();

    tracing::info!("TRC Platform Rust Backend starting...");
    tracing::info!("Environment: {}", config_service.environment().await);

    let server_config = config_service.server().await;
    tracing::info!("Server binding to {}:{}", server_config.host, server_config.port);

    // TODO: Initialize database connection
    // TODO: Initialize application services
    // TODO: Start HTTP server

    println!("TRC Platform Rust Backend - Development Mode");
    println!("Configuration loaded successfully");

    Ok(())
}

// Helper for Box<dyn tracing_subscriber::Layer<...>>
trait BoxedLayer: tracing_subscriber::Layer<()> + Send + Sync + 'static {}
impl<T> BoxedLayer for T where T: tracing_subscriber::Layer<()> + Send + Sync + 'static {}

trait BoxExt {
    fn boxed(self) -> Box<dyn BoxedLayer>;
}
impl<T> BoxExt for T where T: tracing_subscriber::Layer<()> + Send + Sync + 'static {
    fn boxed(self) -> Box<dyn BoxedLayer> {
        Box::new(self)
    }
}
```

## Verification Steps

1. **Configuration Loading Test**:
   ```bash
   cd backend-rs
   cargo run
   # Should load configuration successfully
   ```

2. **Environment Variable Test**:
   ```bash
   export TRC_SERVER__PORT=9090
   export TRC_LOGGING__LEVEL=debug
   cargo run
   # Should use overridden values
   ```

3. **Configuration Validation Test**:
   ```bash
   export TRC_JWT__SECRET="short"
   cargo run
   # Should fail with validation error
   ```

4. **Environment-Specific Test**:
   ```bash
   export TRC_ENVIRONMENT=production
   cargo run
   # Should load production configuration
   ```

5. **JSON Configuration Test**:
   ```bash
   echo '{"server": {"port": 8081}}' > config/override.json
   cargo run
   # Should use overridden port
   ```

## Expected Files Created/Modified

### New Files:
- `config/default.toml`
- `config/development.toml`
- `config/test.toml`
- `config/production.toml`
- `config/local.toml.example`
- `src/config/service.rs`
- `docs/configuration.md`

### Modified Files:
- `src/config/settings.rs` (completely rewritten)
- `src/config/mod.rs` (updated)
- `src/main.rs` (updated to use ConfigService)
- `Cargo.toml` (add figment dependency if not present)

## Configuration Testing

```bash
# Test different environments
TRC_ENVIRONMENT=development cargo run
TRC_ENVIRONMENT=test cargo run
TRC_ENVIRONMENT=production cargo run

# Test environment variables
TRC_SERVER__PORT=9999 cargo run
TRC_DATABASE__MAX_CONNECTIONS=100 cargo run

# Test validation (should fail)
TRC_JWT__SECRET=short cargo run
```

## Next Task Dependency

This task enables:
- **Task 4**: Domain Models (requires configuration validation)
- **Task 5**: Repositories (requires database configuration)
- **Task 6**: Authentication (requires JWT configuration)
- All subsequent tasks that need configuration

## Troubleshooting

- **Configuration Loading Fails**: Check TOML syntax and file permissions
- **Validation Errors**: Ensure all required fields are present and valid
- **Environment Variables Not Working**: Verify `TRC_` prefix and double underscore format
- **Missing Config Files**: Ensure default.toml exists and is readable

## Success Metrics

- [ ] Configuration loads from all sources (files, env vars)
- [ ] Validation catches invalid configuration
- [ ] Environment-specific configs work correctly
- [ ] Sensitive data is not logged
- [ ] Hot-reload works in development mode
- [ ] All default values are sensible
- [ ] Configuration documentation is complete

---

**This task provides a robust, type-safe configuration system that supports multiple environments and validation.**
