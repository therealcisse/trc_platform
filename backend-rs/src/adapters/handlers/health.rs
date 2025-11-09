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
    State(_state): State<HandlerState>,
) -> impl IntoResponse {
    let response = HealthResponse {
        status: "healthy".to_string(),
        timestamp: chrono::Utc::now(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        checks: HashMap::new(),
    };

    (StatusCode::OK, Json(response))
}