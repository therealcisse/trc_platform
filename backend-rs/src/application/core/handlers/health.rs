//! Health check handler

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub timestamp: String,
    pub version: String,
    pub services: ServiceHealth,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ServiceHealth {
    pub database: String,
    pub cache: String,
    pub email: String,
}

pub async fn health_check(
    State(_state): State<crate::HandlerState>,
) -> impl IntoResponse {
    // TODO: Implement comprehensive health checks
    tracing::info!("Health check requested");

    let response = HealthResponse {
        status: "healthy".to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        services: ServiceHealth {
            database: "healthy".to_string(),
            cache: "healthy".to_string(),
            email: "healthy".to_string(),
        },
    };

    (StatusCode::OK, Json(response)).into_response()
}