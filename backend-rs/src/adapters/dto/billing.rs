//! Billing DTOs

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct SubscriptionResponse {
    pub id: String,
    pub status: String,
    pub plan_id: String,
}