//! Settings model

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Settings {
    pub id: i64,
    pub cost_per_request_cents: i32,
    pub openai_model: Option<String>,
    pub openai_timeout_s: i32,
    pub app_domain: Option<String>,
    pub updated_at: DateTime<Utc>,
}