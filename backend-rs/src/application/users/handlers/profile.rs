//! User profile handlers

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct UserProfileResponse {
    pub id: String,
    pub email: String,
    pub full_name: String,
}

pub async fn get_profile(
    State(_state): State<crate::HandlerState>,
) -> impl IntoResponse {
    let response = UserProfileResponse {
        id: "user-id".to_string(),
        email: "user@example.com".to_string(),
        full_name: "John Doe".to_string(),
    };

    (StatusCode::OK, Json(response)).into_response()
}