//! Application info handler

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct InfoResponse {
    pub name: String,
    pub version: String,
    pub description: String,
    pub authors: Vec<String>,
    pub environment: String,
}

pub async fn app_info(
    State(_state): State<crate::HandlerState>,
) -> impl IntoResponse {
    tracing::info!("App info requested");

    let response = InfoResponse {
        name: "TRC Platform".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        description: "API Request Counter Platform".to_string(),
        authors: vec!["TRC Platform Team".to_string()],
        environment: std::env::var("APP_ENVIRONMENT").unwrap_or_else(|_| "development".to_string()),
    };

    (StatusCode::OK, Json(response)).into_response()
}