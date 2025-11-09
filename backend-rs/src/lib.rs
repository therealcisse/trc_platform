//! TRC Platform Rust Backend
//!
//! A high-performance backend for mathematical problem-solving services
//! built with Rust, Axum, and modern async patterns.

pub mod config;
pub mod domain;
pub mod application;
pub mod infrastructure;
pub mod adapters;
pub mod security;

// Re-export HandlerState for convenience
pub use adapters::HandlerState;

use thiserror::Error;

/// Common application errors
#[derive(Debug, Error)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Authentication error: {0}")]
    Authentication(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Internal server error: {0}")]
    Internal(String),
}

impl axum::response::IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            AppError::Database(ref e) => {
                tracing::error!("Database error: {:?}", e);
                (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            }
            AppError::Config(ref msg) => {
                tracing::error!("Configuration error: {}", msg);
                (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Configuration error")
            }
            AppError::Authentication(ref msg) => {
                (axum::http::StatusCode::UNAUTHORIZED, msg.as_str())
            }
            AppError::Validation(ref msg) => {
                (axum::http::StatusCode::BAD_REQUEST, msg.as_str())
            }
            AppError::NotFound(ref msg) => {
                (axum::http::StatusCode::NOT_FOUND, msg.as_str())
            }
            AppError::Internal(ref msg) => {
                tracing::error!("Internal error: {}", msg);
                (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            }
        };

        let body = axum::Json(serde_json::json!({
            "error": error_message
        }));

        (status, body).into_response()
    }
}

