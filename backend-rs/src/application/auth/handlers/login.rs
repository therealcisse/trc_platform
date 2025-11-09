//! Login handler

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct LoginRequest {
    pub email: String,
    pub password: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LoginResponse {
    pub id: String,
    pub email: String,
    pub token: String,
}

pub async fn login(
    State(_state): State<crate::HandlerState>,
    Json(payload): Json<LoginRequest>,
) -> impl IntoResponse {
    // TODO: Implement login logic
    tracing::info!("Login request for: {}", payload.email);

    let response = LoginResponse {
        id: "user-id".to_string(),
        email: payload.email,
        token: "jwt-token".to_string(),
    };

    (StatusCode::OK, Json(response)).into_response()
}