//! Core domain events

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Problem solved event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProblemSolvedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub problem_id: Uuid,
    pub user_id: Uuid,
    pub result: String,
}