//! Invoice handlers

use axum::{
    extract::{State, Path},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct InvoiceResponse {
    pub id: String,
    pub amount: f64,
    pub status: String,
    pub due_date: String,
}

pub async fn get_invoice(
    State(_state): State<crate::HandlerState>,
    Path(invoice_id): Path<String>,
) -> impl IntoResponse {
    // TODO: Implement invoice retrieval
    tracing::info!("Getting invoice: {}", invoice_id);

    let response = InvoiceResponse {
        id: invoice_id,
        amount: 99.99,
        status: "pending".to_string(),
        due_date: "2024-12-31".to_string(),
    };

    (StatusCode::OK, Json(response)).into_response()
}