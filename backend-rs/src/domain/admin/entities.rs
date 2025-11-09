//! Admin domain entities

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Invite code entity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InviteCode {
    id: Uuid,
    code: String,
    created_by: Option<Uuid>,
    used_by: Option<Uuid>,
    max_uses: i32,
    times_used: i32,
    expires_at: Option<DateTime<Utc>>,
    status: InviteStatus,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
    version: i64,
}

/// Invite status enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum InviteStatus {
    Unused,
    Used,
    Expired,
}

/// Application settings entity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    id: Uuid,
    key: String,
    value: Option<String>,
    description: Option<String>,
    is_public: bool,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
    version: i64,
}

impl InviteCode {
    pub fn new(code: String, max_uses: i32, expires_at: Option<DateTime<Utc>>, created_by: Option<Uuid>) -> Self {
        Self {
            id: Uuid::new_v4(),
            code,
            created_by,
            used_by: None,
            max_uses,
            times_used: 0,
            expires_at,
            status: InviteStatus::Unused,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: 1,
        }
    }

    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn code(&self) -> &str {
        &self.code
    }

    pub fn is_available(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            Utc::now() > expires_at || self.times_used >= self.max_uses
        } else {
            self.times_used >= self.max_uses
        }
    }

    pub fn use_invite(&mut self, user_id: Uuid) -> bool {
        if self.is_available() {
            return false;
        }

        self.used_by = Some(user_id);
        self.times_used += 1;
        self.status = InviteStatus::Used;
        self.updated_at = Utc::now();

        true
    }
}

impl Settings {
    pub fn new(key: String, value: Option<String>, description: Option<String>, is_public: bool) -> Self {
        Self {
            id: Uuid::new_v4(),
            key,
            value,
            description,
            is_public,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: 1,
        }
    }

    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn key(&self) -> &str {
        &self.key
    }

    pub fn value(&self) -> Option<&str> {
        self.value.as_deref()
    }

    pub fn is_public(&self) -> bool {
        self.is_public
    }

    pub fn update_value(&mut self, value: String) {
        self.value = Some(value);
        self.updated_at = Utc::now();
        self.version += 1;
    }
}

impl Default for Settings {
    fn default() -> Self {
        Self::new(
            "default".to_string(),
            Some("default_value".to_string()),
            Some("Default setting".to_string()),
            false,
        )
    }
}