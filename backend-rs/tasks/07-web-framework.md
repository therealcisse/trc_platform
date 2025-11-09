# Task 7: Web Framework and HTTP Layer

## Description
Set up the Axum web framework with comprehensive middleware, routing, error handling, and HTTP infrastructure. This task creates the foundation for all HTTP endpoints with proper request/response handling, validation, and error responses.

## Acceptance Criteria
1. ✅ Create Axum application with proper configuration
2. ✅ Implement comprehensive error handling and response formatting
3. ✅ Set up middleware stack (CORS, security, logging, tracing)
4. ✅ Create routing structure for all API domains
5. ✅ Implement request validation and response serialization
6. ✅ Add health check and monitoring endpoints
7. ✅ Configure proper HTTP client for external services

## Prerequisites
- **Task 1**: Project Setup (completed - for Axum dependencies)
- **Task 3**: Configuration (completed - for server settings)
- **Task 6**: Authentication (completed - for security middleware)

## Technical Implementation

### Step 1: Application Structure

#### src/main.rs (update)
```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use trc_platform::{
    config::ConfigService,
    security::{JwtService, AuthState},
    infrastructure::database::connection,
    adapters::handlers,
    adapters::middleware,
};
use axum::{
    Router,
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use std::net::SocketAddr;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load configuration
    let config_service = Arc::new(ConfigService::new().await?);

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

    // Initialize database
    let database_pool = connection::create_pool(&config_service.database().await).await?;
    connection::run_migrations(&database_pool).await?;

    // Initialize services
    let jwt_service = Arc::new(JwtService::new(config_service.jwt().await)?);
    let auth_state = AuthState::new(jwt_service, config_service.clone());

    // Create application
    let app = create_app(auth_state, config_service.clone()).await?;

    // Start server
    let server_config = config_service.server().await;
    let bind_address = format!("{}:{}", server_config.host, server_config.port)
        .parse::<SocketAddr>()?;

    tracing::info!("Server binding to {}", bind_address);

    let listener = tokio::net::TcpListener::bind(bind_address).await?;
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    tracing::info!("Server shutdown complete");
    Ok(())
}

/// Create the Axum application
async fn create_app(
    auth_state: AuthState,
    config_service: Arc<ConfigService>,
) -> Result<Router, Box<dyn std::error::Error>> {
    // Create handler state
    let handler_state = handlers::HandlerState::new(auth_state, config_service).await?;

    // Build router
    let app = Router::new()
        // Health and monitoring endpoints
        .route("/health", axum::handlers::get(handlers::health::health_check))
        .route("/health/detailed", axum::handlers::get(handlers::health::detailed_health))

        // API routes
        .nest("/api/v1", api_routes())
        .nest("/api", api_routes())

        // Global middleware
        .layer(
            tower::ServiceBuilder::new()
                .layer(middleware::cors_middleware())
                .layer(middleware::security_headers_middleware())
                .layer(middleware::request_tracing_middleware())
                .layer(middleware::error_handling_middleware())
        )
        .with_state(handler_state);

    Ok(app)
}

/// API routes
fn api_routes() -> Router<handlers::HandlerState> {
    Router::new()
        // User routes
        .nest("/users", handlers::users::user_routes())

        // Auth routes
        .nest("/auth", handlers::auth::auth_routes())

        // Core routes
        .nest("/core", handlers::core::core_routes())

        // Billing routes
        .nest("/billing", handlers::billing::billing_routes())

        // Usage routes
        .nest("/usage", handlers::usage::usage_routes())

        // Admin routes
        .nest("/admin", handlers::admin::admin_routes())
}

/// Graceful shutdown signal
async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {
            tracing::info!("Received Ctrl+C signal");
        },
        _ = terminate => {
            tracing::info!("Received terminate signal");
        },
    }
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

### Step 2: Handler Foundation

#### src/adapters/mod.rs
```rust
//! Adapters layer - HTTP handlers and external integrations

pub mod handlers;
pub mod middleware;
pub mod dto;
pub mod error;
pub mod client;

pub use handlers::*;
pub use middleware::*;
pub use dto::*;
pub use error::*;
pub use client::*;
```

#### src/adapters/handlers/mod.rs
```rust
//! HTTP handlers module

pub mod health;
pub mod users;
pub mod auth;
pub mod core;
pub mod billing;
pub mod usage;
pub mod admin;

use std::sync::Arc;
use crate::{
    config::ConfigService,
    security::AuthState,
    infrastructure::database::repositories::RepositoryManager,
};

/// Handler state shared across all handlers
#[derive(Clone)]
pub struct HandlerState {
    pub auth_state: AuthState,
    pub config_service: Arc<ConfigService>,
    pub repository_manager: Arc<RepositoryManager>,
}

impl HandlerState {
    pub async fn new(
        auth_state: AuthState,
        config_service: Arc<ConfigService>,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        // Create database pool
        let database_pool = crate::infrastructure::database::connection::create_pool(
            &config_service.database().await
        ).await?;

        // Create repository manager
        let repository_manager = Arc::new(RepositoryManager::new(database_pool));

        Ok(Self {
            auth_state,
            config_service,
            repository_manager,
        })
    }

    // Convenience methods for accessing repositories
    pub fn users(&self) -> &crate::infrastructure::database::repositories::UserRepository {
        self.repository_manager.users()
    }

    pub fn api_tokens(&self) -> &crate::infrastructure::database::repositories::ApiTokenRepository {
        self.repository_manager.api_tokens()
    }

    pub fn billing_periods(&self) -> &crate::infrastructure::database::repositories::BillingPeriodRepository {
        self.repository_manager.billing_periods()
    }

    pub fn request_logs(&self) -> &crate::infrastructure::database::repositories::RequestLogRepository {
        self.repository_manager.request_logs()
    }

    pub fn invite_codes(&self) -> &crate::infrastructure::database::repositories::InviteCodeRepository {
        self.repository_manager.invite_codes()
    }
}
```

#### src/adapters/handlers/health.rs
```rust
//! Health check handlers

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use crate::adapters::HandlerState;
use crate::infrastructure::database::Database;

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub version: String,
    pub checks: HashMap<String, HealthCheck>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheck {
    pub status: String,
    pub message: Option<String>,
    pub duration_ms: Option<u64>,
}

/// Basic health check
pub async fn health_check() -> impl IntoResponse {
    let response = HealthResponse {
        status: "healthy".to_string(),
        timestamp: chrono::Utc::now(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        checks: HashMap::new(),
    };

    (StatusCode::OK, Json(response))
}

/// Detailed health check with all service dependencies
pub async fn detailed_health(
    State(state): State<HandlerState>,
) -> impl IntoResponse {
    let mut checks = HashMap::new();
    let overall_status = "healthy";

    // Check database connectivity
    let db_check = check_database(&state).await;
    checks.insert("database".to_string(), db_check);

    // Check configuration
    let config_check = check_configuration(&state).await;
    checks.insert("configuration".to_string(), config_check);

    // Check JWT service
    let jwt_check = check_jwt_service(&state).await;
    checks.insert("jwt".to_string(), jwt_check);

    // Determine overall status
    let overall_status = if checks.values().all(|check| check.status == "healthy") {
        "healthy"
    } else {
        "unhealthy"
    };

    let status_code = if overall_status == "healthy" {
        StatusCode::OK
    } else {
        StatusCode::SERVICE_UNAVAILABLE
    };

    let response = HealthResponse {
        status: overall_status.to_string(),
        timestamp: chrono::Utc::now(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        checks,
    };

    (status_code, Json(response))
}

async fn check_database(state: &HandlerState) -> HealthCheck {
    let start = std::time::Instant::now();

    // This would require access to the database pool
    // For now, we'll simulate the check
    let is_healthy = true; // TODO: Implement actual database health check

    let duration = start.elapsed().as_millis() as u64;

    HealthCheck {
        status: if is_healthy { "healthy" } else { "unhealthy" }.to_string(),
        message: if is_healthy {
            None
        } else {
            Some("Database connection failed".to_string())
        },
        duration_ms: Some(duration),
    }
}

async fn check_configuration(state: &HandlerState) -> HealthCheck {
    let start = std::time::Instant::now();

    // Check if configuration is loaded and valid
    let config = state.config_service.get().await;
    let is_healthy = config.validate().is_ok();

    let duration = start.elapsed().as_millis() as u64;

    HealthCheck {
        status: if is_healthy { "healthy" } else { "unhealthy" }.to_string(),
        message: if is_healthy {
            None
        } else {
            Some("Configuration validation failed".to_string())
        },
        duration_ms: Some(duration),
    }
}

async fn check_jwt_service(state: &HandlerState) -> HealthCheck {
    let start = std::time::Instant::now();

    // Test JWT service by creating and validating a token
    let test_user_id = uuid::Uuid::new_v4();
    let token_result = state.auth_state.jwt_service.generate_access_token(
        test_user_id,
        vec!["test".to_string()],
    );

    let is_healthy = token_result.is_ok();
    let duration = start.elapsed().as_millis() as u64;

    HealthCheck {
        status: if is_healthy { "healthy" } else { "unhealthy" }.to_string(),
        message: if is_healthy {
            None
        } else {
            Some("JWT service failed".to_string())
        },
        duration_ms: Some(duration),
    }
}
```

### Step 3: Error Handling

#### src/adapters/error.rs
```rust
//! HTTP error handling and response formatting

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use thiserror::Error;
use crate::AppError;
use crate::security::SecurityError;

/// API Error response structure
#[derive(Debug, Serialize)]
pub struct ApiError {
    pub error: String,
    pub message: Option<String>,
    pub code: Option<String>,
    pub details: Option<serde_json::Value>,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl ApiError {
    pub fn new(error: String) -> Self {
        Self {
            error,
            message: None,
            code: None,
            details: None,
            timestamp: chrono::Utc::now(),
        }
    }

    pub fn with_message(mut self, message: String) -> Self {
        self.message = Some(message);
        self
    }

    pub fn with_code(mut self, code: String) -> Self {
        self.code = Some(code);
        self
    }

    pub fn with_details(mut self, details: serde_json::Value) -> Self {
        self.details = Some(details);
        self
    }
}

/// Convert AppError to HTTP response
impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error) = match self {
            AppError::Database(ref e) => {
                tracing::error!("Database error: {:?}", e);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ApiError::new("database_error".to_string())
                        .with_message("Internal database error".to_string()),
                )
            }
            AppError::Config(ref msg) => {
                tracing::error!("Configuration error: {}", msg);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ApiError::new("configuration_error".to_string())
                        .with_message("Configuration error".to_string()),
                )
            }
            AppError::Authentication(ref msg) => {
                (
                    StatusCode::UNAUTHORIZED,
                    ApiError::new("authentication_error".to_string())
                        .with_message(msg.clone()),
                )
            }
            AppError::Validation(ref msg) => {
                (
                    StatusCode::BAD_REQUEST,
                    ApiError::new("validation_error".to_string())
                        .with_message(msg.clone()),
                )
            }
            AppError::NotFound(ref msg) => {
                (
                    StatusCode::NOT_FOUND,
                    ApiError::new("not_found".to_string())
                        .with_message(msg.clone()),
                )
            }
            AppError::Internal(ref msg) => {
                tracing::error!("Internal error: {}", msg);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ApiError::new("internal_error".to_string())
                        .with_message("Internal server error".to_string()),
                )
            }
        };

        (status, Json(error)).into_response()
    }
}

/// Convert SecurityError to HTTP response
impl IntoResponse for SecurityError {
    fn into_response(self) -> Response {
        let (status, error) = match self {
            SecurityError::InvalidToken(ref msg) => {
                (
                    StatusCode::UNAUTHORIZED,
                    ApiError::new("invalid_token".to_string())
                        .with_message(msg.clone())
                        .with_code("AUTH_001".to_string()),
                )
            }
            SecurityError::TokenExpired => {
                (
                    StatusCode::UNAUTHORIZED,
                    ApiError::new("token_expired".to_string())
                        .with_message("Token has expired".to_string())
                        .with_code("AUTH_002".to_string()),
                )
            }
            SecurityError::InvalidCredentials => {
                (
                    StatusCode::UNAUTHORIZED,
                    ApiError::new("invalid_credentials".to_string())
                        .with_message("Invalid credentials".to_string())
                        .with_code("AUTH_003".to_string()),
                )
            }
            SecurityError::AccessDenied(ref msg) => {
                (
                    StatusCode::FORBIDDEN,
                    ApiError::new("access_denied".to_string())
                        .with_message(msg.clone())
                        .with_code("AUTH_004".to_string()),
                )
            }
            SecurityError::InsufficientPermissions => {
                (
                    StatusCode::FORBIDDEN,
                    ApiError::new("insufficient_permissions".to_string())
                        .with_message("Insufficient permissions".to_string())
                        .with_code("AUTH_005".to_string()),
                )
            }
            SecurityError::AccountDisabled => {
                (
                    StatusCode::FORBIDDEN,
                    ApiError::new("account_disabled".to_string())
                        .with_message("Account is disabled".to_string())
                        .with_code("AUTH_006".to_string()),
                )
            }
            SecurityError::RateLimitExceeded => {
                (
                    StatusCode::TOO_MANY_REQUESTS,
                    ApiError::new("rate_limit_exceeded".to_string())
                        .with_message("Rate limit exceeded".to_string())
                        .with_code("AUTH_007".to_string()),
                )
            }
            SecurityError::Internal(ref msg) => {
                tracing::error!("Security internal error: {}", msg);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    ApiError::new("security_error".to_string())
                        .with_message("Internal security error".to_string())
                        .with_code("AUTH_008".to_string()),
                )
            }
        };

        (status, Json(error)).into_response()
    }
}

/// HTTP validation error
#[derive(Debug, Error)]
pub enum HttpValidationError {
    #[error("Invalid JSON: {0}")]
    InvalidJson(#[from] serde_json::Error),

    #[error("Missing required field: {0}")]
    MissingField(String),

    #[error("Invalid field: {field} - {message}")]
    InvalidField { field: String, message: String },

    #[error("Query parameter error: {0}")]
    QueryParameterError(String),

    #[error("Path parameter error: {0}")]
    PathParameterError(String),

    #[error("Invalid content type")]
    InvalidContentType,

    #[error("Request body too large")]
    PayloadTooLarge,
}

impl IntoResponse for HttpValidationError {
    fn into_response(self) -> Response {
        let (status, error) = match self {
            HttpValidationError::InvalidJson(ref e) => {
                (
                    StatusCode::BAD_REQUEST,
                    ApiError::new("invalid_json".to_string())
                        .with_message("Invalid JSON format".to_string())
                        .with_details(json!({
                            "validation_error": e.to_string()
                        })),
                )
            }
            HttpValidationError::MissingField(ref field) => {
                (
                    StatusCode::BAD_REQUEST,
                    ApiError::new("missing_field".to_string())
                        .with_message(format!("Missing required field: {}", field))
                        .with_code("VALIDATION_001".to_string()),
                )
            }
            HttpValidationError::InvalidField { ref field, ref message } => {
                (
                    StatusCode::BAD_REQUEST,
                    ApiError::new("invalid_field".to_string())
                        .with_message(format!("Invalid field: {}", field))
                        .with_details(json!({
                            "field": field,
                            "message": message
                        }))
                        .with_code("VALIDATION_002".to_string()),
                )
            }
            HttpValidationError::QueryParameterError(ref msg) => {
                (
                    StatusCode::BAD_REQUEST,
                    ApiError::new("query_parameter_error".to_string())
                        .with_message(msg.clone())
                        .with_code("VALIDATION_003".to_string()),
                )
            }
            HttpValidationError::PathParameterError(ref msg) => {
                (
                    StatusCode::NOT_FOUND,
                    ApiError::new("path_parameter_error".to_string())
                        .with_message(msg.clone())
                        .with_code("VALIDATION_004".to_string()),
                )
            }
            HttpValidationError::InvalidContentType => {
                (
                    StatusCode::UNSUPPORTED_MEDIA_TYPE,
                    ApiError::new("invalid_content_type".to_string())
                        .with_message("Unsupported content type".to_string())
                        .with_code("VALIDATION_005".to_string()),
                )
            }
            HttpValidationError::PayloadTooLarge => {
                (
                    StatusCode::PAYLOAD_TOO_LARGE,
                    ApiError::new("payload_too_large".to_string())
                        .with_message("Request body too large".to_string())
                        .with_code("VALIDATION_006".to_string()),
                )
            }
        };

        (status, Json(error)).into_response()
    }
}

/// Result type for HTTP handlers
pub type HttpResult<T> = Result<T, HttpError>;

/// HTTP error enum that encompasses all possible errors
#[derive(Debug, Error)]
pub enum HttpError {
    #[error("Application error: {0}")]
    App(#[from] AppError),

    #[error("Security error: {0}")]
    Security(#[from] SecurityError),

    #[error("Validation error: {0}")]
    Validation(#[from] HttpValidationError),

    #[error("Not found: {0}")]
    NotFound(String),
}

impl IntoResponse for HttpError {
    fn into_response(self) -> Response {
        match self {
            HttpError::App(err) => err.into_response(),
            HttpError::Security(err) => err.into_response(),
            HttpError::Validation(err) => err.into_response(),
            HttpError::NotFound(msg) => {
                (
                    StatusCode::NOT_FOUND,
                    Json(ApiError::new("not_found".to_string())
                        .with_message(msg)
                        .with_code("NOT_FOUND_001".to_string())),
                )
                    .into_response()
            }
        }
    }
}

/// Convert domain errors to HTTP errors
impl From<crate::domain::DomainError> for HttpError {
    fn from(err: crate::domain::DomainError) -> Self {
        match err {
            crate::domain::DomainError::ValidationError { field, message } => {
                HttpError::Validation(HttpValidationError::InvalidField {
                    field,
                    message,
                })
            }
            crate::domain::DomainError::BusinessRuleViolation { rule } => {
                HttpError::App(AppError::Validation(rule))
            }
            crate::domain::DomainError::NotFound { entity, id } => {
                HttpError::NotFound(format!("{} with id {} not found", entity, id))
            }
            crate::domain::DomainError::Duplicate { entity, value } => {
                HttpError::App(AppError::Validation(format!("{} with value {} already exists", entity, value)))
            }
            crate::domain::DomainError::AccessDenied { reason } => {
                HttpError::Security(SecurityError::AccessDenied(reason))
            }
            crate::domain::DomainError::OperationNotAllowed { operation } => {
                HttpError::Security(SecurityError::InsufficientPermissions)
            }
        }
    }
}
```

### Step 4: Middleware

#### src/adapters/middleware/mod.rs
```rust
//! HTTP middleware implementations

pub mod auth;
pub mod cors;
pub mod error_handling;
pub mod tracing;
pub mod security_headers;
pub mod rate_limiting;

pub use auth::*;
pub use cors::*;
pub use error_handling::*;
pub use tracing::*;
pub use security_headers::*;
pub use rate_limiting::*;

use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};
use tower::ServiceBuilder;
use tower_http::{
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};

/// CORS middleware
pub fn cors_middleware() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([
            axum::http::Method::GET,
            axum::http::Method::POST,
            axum::http::Method::PUT,
            axum::http::Method::DELETE,
            axum::http::Method::OPTIONS,
        ])
        .allow_headers(Any)
        .allow_credentials(true)
        .max_age(std::time::Duration::from_secs(3600))
}

/// Request tracing middleware
pub fn request_tracing_middleware() -> TraceLayer<axum::extract::Request> {
    TraceLayer::new_for_http()
        .make_request_with_id(|request: &Request<_>| {
            // Extract or generate request ID
            request
                .headers()
                .get("x-request-id")
                .and_then(|h| h.to_str().ok())
                .map(|s| s.to_string())
                .unwrap_or_else(|| uuid::Uuid::new_v4().to_string())
                .into()
        })
        .on_request(|_request, _span, _level| {
            tracing::debug!("Request started");
        })
        .on_response(|_response, _latency, _span| {
            tracing::debug!("Response sent");
        })
}

/// Security headers middleware
pub async fn security_headers_middleware(
    request: Request,
    next: Next,
) -> Response {
    let mut response = next.run(request).await;

    // Add security headers
    let headers = response.headers_mut();

    headers.insert("X-Content-Type-Options", "nosniff".parse().unwrap());
    headers.insert("X-Frame-Options", "DENY".parse().unwrap());
    headers.insert("X-XSS-Protection", "1; mode=block".parse().unwrap());
    headers.insert("Referrer-Policy", "strict-origin-when-cross-origin".parse().unwrap());

    // Add HSTS header in production
    headers.insert("Strict-Transport-Security", "max-age=31536000; includeSubDomains".parse().unwrap());

    // Add CSP header
    headers.insert("Content-Security-Policy", "default-src 'self'".parse().unwrap());

    response
}

/// Error handling middleware
pub fn error_handling_middleware() -> tower::layer::util::Stack<
    axum::middleware::FromFnLayer<impl Fn(Request) -> Result<Response, axum::response::Response> + Clone>,
    axum::layer::util::Stack<
        axum::middleware::FromFnLayer<impl Fn(Request) -> Result<Response, axum::response::Response> + Clone>,
        tower::layer::util::Identity,
    >,
> {
    ServiceBuilder::new()
        .layer(axum::middleware::from_fn(error_response_middleware))
        .layer(axum::middleware::from_fn(panic_handler_middleware))
}

/// Convert unhandled errors to proper HTTP responses
async fn error_response_middleware(
    request: Request,
    next: Next,
) -> Result<Response, axum::response::Response> {
    let response = next.run(request).await;

    // If response is already an error response, return as-is
    if response.status().is_client_error() || response.status().is_server_error() {
        return Ok(response);
    }

    Ok(response)
}

/// Handle panics in middleware
async fn panic_handler_middleware(
    request: Request,
    next: Next,
) -> Result<Response, axum::response::Response> {
    // Use std::panic::catch_unwind to catch panics
    std::panic::catch_unwind(move || {
        tokio::task::block_in_place(|| {
            tokio::runtime::Handle::current().block_on(next.run(request))
        })
    })
    .map_err(|_| {
        tracing::error!("Panic caught in middleware");
        axum::response::Response::builder()
            .status(axum::http::StatusCode::INTERNAL_SERVER_ERROR)
            .body(axum::body::Body::from("Internal server error"))
            .unwrap()
    })?
}
```

### Step 5: HTTP Client

#### src/adapters/client/mod.rs
```rust
//! HTTP client for external API calls

use reqwest::{Client, RequestBuilder};
use std::time::Duration;
use crate::config::ConfigService;
use crate::adapters::error::HttpError;

/// HTTP client wrapper with configuration
#[derive(Clone)]
pub struct HttpClient {
    client: Client,
    config_service: std::sync::Arc<ConfigService>,
}

impl HttpClient {
    /// Create new HTTP client with configuration
    pub async fn new(config_service: std::sync::Arc<ConfigService>) -> Result<Self, HttpError> {
        let server_config = config_service.server().await;

        let client = Client::builder()
            .timeout(Duration::from_millis(server_config.request_timeout_ms))
            .connect_timeout(Duration::from_millis(5000))
            .pool_max_idle_per_host(10)
            .pool_idle_timeout(Duration::from_secs(30))
            .user_agent(format!("trc-platform/{}", env!("CARGO_PKG_VERSION")))
            .build()
            .map_err(|e| HttpError::App(crate::AppError::Internal(format!("Failed to create HTTP client: {}", e))))?;

        Ok(Self {
            client,
            config_service,
        })
    }

    /// Get underlying reqwest client
    pub fn client(&self) -> &Client {
        &self.client
    }

    /// Make GET request
    pub async fn get(&self, url: &str) -> RequestBuilder {
        self.client.get(url)
    }

    /// Make POST request
    pub async fn post(&self, url: &str) -> RequestBuilder {
        self.client.post(url)
    }

    /// Make PUT request
    pub async fn put(&self, url: &str) -> RequestBuilder {
        self.client.put(url)
    }

    /// Make DELETE request
    pub async fn delete(&self, url: &str) -> RequestBuilder {
        self.client.delete(url)
    }

    /// Make PATCH request
    pub async fn patch(&self, url: &str) -> RequestBuilder {
        self.client.patch(url)
    }
}

/// HTTP response wrapper
#[derive(Debug)]
pub struct HttpResponse {
    pub status: reqwest::StatusCode,
    pub headers: reqwest::header::HeaderMap,
    pub body: String,
}

impl HttpResponse {
    /// Convert reqwest response to our wrapper
    pub async fn from_reqwest(response: reqwest::Response) -> Result<Self, HttpError> {
        let status = response.status();
        let headers = response.headers().clone();

        let body = response.text().await
            .map_err(|e| HttpError::App(crate::AppError::Internal(format!("Failed to read response body: {}", e))))?;

        Ok(Self {
            status,
            headers,
            body,
        })
    }

    /// Check if response is successful
    pub fn is_success(&self) -> bool {
        self.status.is_success()
    }

    /// Get response as JSON
    pub fn json<T: serde::de::DeserializeOwned>(&self) -> Result<T, HttpError> {
        serde_json::from_str(&self.body)
            .map_err(|e| HttpError::App(crate::AppError::Internal(format!("Failed to parse JSON: {}", e))))
    }
}
```

## Verification Steps

1. **Web Framework Compilation**:
   ```bash
   cd backend-rs
   cargo check
   # Should compile without errors
   ```

2. **Health Check Tests**:
   ```bash
   cargo test handlers::health
   # Test health check endpoints
   ```

3. **Error Handling Tests**:
   ```bash
   cargo test adapters::error
   # Test error response formatting
   ```

4. **Middleware Tests**:
   ```bash
   cargo test adapters::middleware
   # Test middleware functionality
   ```

## Expected Files Created

### New Files:
- `src/adapters/mod.rs`
- `src/adapters/handlers/mod.rs`
- `src/adapters/handlers/health.rs`
- `src/adapters/error.rs`
- `src/adapters/middleware/mod.rs`
- `src/adapters/client/mod.rs`

### Modified Files:
- `src/main.rs` (significant update with web framework setup)
- `Cargo.toml` (ensure axum and tower dependencies)

## Next Task Dependency

This task enables:
- **Task 8**: User Management (requires web framework foundation)
- **Task 9**: Core Service (requires HTTP client)
- **Task 10**: Billing System (requires web framework)
- **Task 11**: Admin Endpoints (requires web framework)
- All subsequent API endpoint implementations

## Success Metrics

- [ ] Axum application starts successfully
- [ ] Health check endpoints return proper responses
- [ ] Error handling formats responses correctly
- [ ] Middleware stack functions properly
- [ ] CORS configuration works
- [ ] Security headers are set correctly
- [ ] Request tracing and logging works
- [ ] HTTP client is configured and functional
- [ ] Application can be shut down gracefully

---

**This task provides a robust web framework foundation with proper error handling, middleware, and HTTP infrastructure.**