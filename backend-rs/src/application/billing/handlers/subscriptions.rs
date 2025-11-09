//! Subscription handlers

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct CreateSubscriptionRequest {
    pub plan_id: String,
    pub payment_method_id: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SubscriptionResponse {
    pub id: String,
    pub plan_id: String,
    pub status: String,
}

pub async fn create_subscription(
    State(_state): State<crate::HandlerState>,
    Json(payload): Json<CreateSubscriptionRequest>,
) -> impl IntoResponse {
    // TODO: Implement subscription creation
    tracing::info!("Creating subscription for plan: {}", payload.plan_id);

    let response = SubscriptionResponse {
        id: "subscription-id".to_string(),
        plan_id: payload.plan_id,
        status: "active".to_string(),
    };

    (StatusCode::CREATED, Json(response)).into_response()
}