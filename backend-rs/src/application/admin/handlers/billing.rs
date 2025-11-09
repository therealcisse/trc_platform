//! Admin billing handlers

use axum::{
    extract::{State, Query},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct BillingStatsQuery {
    pub period: Option<String>,
    pub start_date: Option<String>,
    pub end_date: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BillingStatsResponse {
    pub total_revenue: f64,
    pub active_subscriptions: u64,
    pub churn_rate: f64,
    pub average_revenue_per_user: f64,
    pub period: String,
}

pub async fn get_billing_stats(
    State(_state): State<crate::HandlerState>,
    Query(query): Query<BillingStatsQuery>,
) -> impl IntoResponse {
    // TODO: Implement billing statistics calculation
    tracing::info!("Admin getting billing stats for period: {:?}", query);

    let response = BillingStatsResponse {
        total_revenue: 9999.99,
        active_subscriptions: 42,
        churn_rate: 0.05,
        average_revenue_per_user: 238.09,
        period: query.period.unwrap_or_else(|| "current_month".to_string()),
    };

    (StatusCode::OK, Json(response)).into_response()
}