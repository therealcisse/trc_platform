//! Billing domain events

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Billing period created event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BillingPeriodCreatedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub period_id: Uuid,
}