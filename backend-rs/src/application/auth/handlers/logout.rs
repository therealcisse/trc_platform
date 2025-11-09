//! Logout handler

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct LogoutResponse {
    pub message: String,
}

pub async fn logout(
    State(_state): State<crate::HandlerState>,
) -> impl IntoResponse {
    // TODO: Implement logout logic
    tracing::info!("Logout request");

    let response = LogoutResponse {
        message: "Logged out successfully".to_string(),
    };

    (StatusCode::OK, Json(response)).into_response()
}