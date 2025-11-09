//! Admin domain events

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Invite code created event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InviteCodeCreatedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub admin_user_id: Uuid,
    pub invite_code: String,
}