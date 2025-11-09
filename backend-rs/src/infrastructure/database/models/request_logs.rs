//! Request log model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct RequestLog {
    pub id: Uuid,
    pub user_id: Uuid,
    pub token_id: Option<Uuid>,
    pub billing_period_id: Option<Uuid>,
    pub service: String,
    pub request_ts: DateTime<Utc>,
    pub duration_ms: i32,
    pub request_bytes: i32,
    pub response_bytes: i32,
    pub status: String,
    pub error_code: Option<String>,
    pub request_id: Uuid,
    pub flow_id: Option<String>,
    pub result: Option<String>,
}