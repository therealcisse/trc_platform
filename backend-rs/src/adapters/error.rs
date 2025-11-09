//! HTTP error handling and response formatting

use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde::Serialize;
use crate::AppError;

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
            AppError::Database(ref _e) => {
                tracing::error!("Database error occurred");
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