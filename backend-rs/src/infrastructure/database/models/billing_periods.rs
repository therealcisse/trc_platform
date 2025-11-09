//! Billing period model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc, NaiveDate};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct BillingPeriod {
    pub id: Uuid,
    pub user_id: Uuid,
    pub period_start: NaiveDate,
    pub period_end: NaiveDate,
    pub total_requests: i32,
    pub total_cost_cents: i32,
    pub is_current: bool,
    pub payment_status: String,
    pub paid_at: Option<DateTime<Utc>>,
    pub paid_amount_cents: Option<i32>,
    pub payment_reference: Option<String>,
    pub notes: Option<String>,
    pub version: Option<i64>,
}