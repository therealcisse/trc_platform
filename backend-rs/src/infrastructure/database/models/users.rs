//! User model with SQLx mappings

use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    pub password_hash: String,
    pub is_active: bool,
    pub is_staff: bool,
    pub email_verified_at: Option<DateTime<Utc>>,
    pub date_joined: DateTime<Utc>,
    pub user_accepted_terms: bool,
    pub user_acknowledged_disclaimer: bool,
    pub version: Option<i64>,
}