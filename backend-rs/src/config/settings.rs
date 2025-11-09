//! Application settings and configuration

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

impl Default for Environment {
    fn default() -> Self {
        Environment::Development
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

/// Configuration service for managing application settings
pub struct ConfigService {
    settings: std::sync::Arc<Settings>,
}

impl ConfigService {
    /// Create a new configuration service
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let settings = Settings::load()?;
        settings.validate().map_err(|e| format!("Configuration validation failed: {}", e))?;

        Ok(Self {
            settings: std::sync::Arc::new(settings),
        })
    }

    /// Create configuration service from existing settings
    pub fn from_settings(settings: Settings) -> Result<Self, Box<dyn std::error::Error>> {
        settings.validate().map_err(|e| format!("Configuration validation failed: {}", e))?;

        Ok(Self {
            settings: std::sync::Arc::new(settings),
        })
    }

    /// Get server settings
    pub fn server(&self) -> &ServerSettings {
        &self.settings.server
    }

    /// Get database settings
    pub async fn database(&self) -> DatabaseSettings {
        self.settings.database.clone()
    }

    /// Get OpenAI settings
    pub fn openai(&self) -> &OpenAISettings {
        &self.settings.openai
    }

    /// Get JWT settings
    pub fn jwt(&self) -> &JwtSettings {
        &self.settings.jwt
    }

    /// Get email settings
    pub fn email(&self) -> &EmailSettings {
        &self.settings.email
    }

    /// Get cache settings
    pub fn cache(&self) -> &CacheSettings {
        &self.settings.cache
    }

    /// Get logging settings
    pub fn logging(&self) -> &LoggingSettings {
        &self.settings.logging
    }

    /// Get CORS settings
    pub fn cors(&self) -> &CorsSettings {
        &self.settings.cors
    }

    /// Get environment
    pub fn environment(&self) -> &Environment {
        &self.settings.environment
    }

    /// Get all settings
    pub fn settings(&self) -> &Settings {
        &self.settings
    }
}