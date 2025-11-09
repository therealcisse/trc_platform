//! User domain events

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// User registered event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserRegisteredEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub email: String,
}

impl UserRegisteredEvent {
    pub fn new(user_id: Uuid, email: String) -> Self {
        Self {
            event_id: Uuid::new_v4(),
            occurred_at: Utc::now(),
            user_id,
            email,
        }
    }
}