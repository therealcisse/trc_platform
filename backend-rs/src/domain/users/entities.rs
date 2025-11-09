//! User domain entity

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use crate::domain::DomainError;

/// User aggregate root
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    id: Uuid,
    email: String,
    password_hash: PasswordHash,
    is_active: bool,
    is_staff: bool,
    email_verified_at: Option<DateTime<Utc>>,
    date_joined: DateTime<Utc>,
    profile: UserProfile,
    version: i64,
}

impl User {
    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn email(&self) -> &str {
        &self.email
    }

    pub fn is_active(&self) -> bool {
        self.is_active
    }

    pub fn is_staff(&self) -> bool {
        self.is_staff
    }

    pub fn is_email_verified(&self) -> bool {
        self.email_verified_at.is_some()
    }
}

/// Password hash value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PasswordHash(String);

impl PasswordHash {
    pub fn new(hash: &str) -> Result<Self, DomainError> {
        if hash.len() > 255 {
            return Err(DomainError::ValidationError {
                field: "password_hash".to_string(),
                message: "Password hash too long (max 255 characters)".to_string(),
            });
        }

        Ok(PasswordHash(hash.to_string()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// User profile value object
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UserProfile {
    pub user_accepted_terms: bool,
    pub user_acknowledged_disclaimer: bool,
}

impl UserProfile {
    pub fn has_accepted_terms(&self) -> bool {
        self.user_accepted_terms
    }

    pub fn has_acknowledged_disclaimer(&self) -> bool {
        self.user_acknowledged_disclaimer
    }
}

impl Default for UserProfile {
    fn default() -> Self {
        UserProfile {
            user_accepted_terms: false,
            user_acknowledged_disclaimer: false,
        }
    }
}

/// API Token domain entity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiToken {
    id: Uuid,
    user_id: Uuid,
    name: String,
    token_hash: String,
    last_used_at: Option<DateTime<Utc>>,
    expires_at: Option<DateTime<Utc>>,
    status: TokenStatus,
    created_at: DateTime<Utc>,
    version: i64,
}

/// Token status enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenStatus {
    Active,
    Revoked,
    Expired,
}

impl ApiToken {
    pub fn new(
        user_id: Uuid,
        name: String,
        token_hash: String,
        expires_at: Option<DateTime<Utc>>,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            user_id,
            name,
            token_hash,
            last_used_at: None,
            expires_at,
            status: TokenStatus::Active,
            created_at: Utc::now(),
            version: 1,
        }
    }

    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn user_id(&self) -> Uuid {
        self.user_id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn is_active(&self) -> bool {
        matches!(self.status, TokenStatus::Active)
    }

    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            Utc::now() > expires_at
        } else {
            false
        }
    }

    pub fn revoke(&mut self) {
        self.status = TokenStatus::Revoked;
    }

    pub fn update_last_used(&mut self) {
        self.last_used_at = Some(Utc::now());
    }
}