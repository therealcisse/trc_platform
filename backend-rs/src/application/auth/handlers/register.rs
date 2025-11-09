//! Register handler

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct RegisterRequest {
    pub email: String,
    pub password: String,
    pub full_name: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RegisterResponse {
    pub id: String,
    pub email: String,
    pub message: String,
}

pub async fn register(
    State(_state): State<crate::HandlerState>,
    Json(payload): Json<RegisterRequest>,
) -> impl IntoResponse {
    // TODO: Implement registration logic
    tracing::info!("Registration request for: {}", payload.email);

    let response = RegisterResponse {
        id: "user-id".to_string(),
        email: payload.email,
        message: "User registered successfully".to_string(),
    };

    (StatusCode::CREATED, Json(response)).into_response()
}