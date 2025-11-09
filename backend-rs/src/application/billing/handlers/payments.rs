//! Payment handlers

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct ProcessPaymentRequest {
    pub invoice_id: String,
    pub payment_method_id: String,
    pub amount: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PaymentResponse {
    pub id: String,
    pub status: String,
    pub amount: f64,
}

pub async fn process_payment(
    State(_state): State<crate::HandlerState>,
    Json(payload): Json<ProcessPaymentRequest>,
) -> impl IntoResponse {
    // TODO: Implement payment processing
    tracing::info!("Processing payment for invoice: {}", payload.invoice_id);

    let response = PaymentResponse {
        id: "payment-id".to_string(),
        status: "completed".to_string(),
        amount: payload.amount,
    };

    (StatusCode::CREATED, Json(response)).into_response()
}