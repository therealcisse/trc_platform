//! Admin repository traits

use async_trait::async_trait;
use crate::domain::DomainError;
use super::entities::{InviteCode, Settings};

/// Invite code repository trait
#[async_trait]
pub trait InviteCodeRepository: Send + Sync {
    /// Find an invite code by its code
    async fn find_by_code(&self, code: &str) -> Result<Option<InviteCode>, DomainError>;

    /// Save an invite code (create or update)
    async fn save(&self, invite_code: &InviteCode) -> Result<(), DomainError>;

    /// Mark an invite code as used by a user
    async fn mark_used(&self, code_id: &str, user_id: &str) -> Result<(), DomainError>;

    /// Find invite codes created by a user
    async fn find_by_creator(&self, created_by: &str) -> Result<Vec<InviteCode>, DomainError>;

    /// Find expired invite codes
    async fn find_expired(&self) -> Result<Vec<InviteCode>, DomainError>;

    /// Delete expired invite codes
    async fn delete_expired(&self) -> Result<u64, DomainError>;

    /// Count available invite codes
    async fn count_available(&self) -> Result<u64, DomainError>;
}

/// Settings repository trait
#[async_trait]
pub trait SettingsRepository: Send + Sync {
    /// Get a setting value by key
    async fn get(&self, key: &str) -> Result<Option<String>, DomainError>;

    /// Set a setting value
    async fn set(&self, key: &str, value: &str) -> Result<(), DomainError>;

    /// Get all settings
    async fn get_all(&self) -> Result<Vec<Settings>, DomainError>;

    /// Get only public settings
    async fn get_public(&self) -> Result<Vec<Settings>, DomainError>;

    /// Update a setting description
    async fn update_description(&self, key: &str, description: &str) -> Result<(), DomainError>;

    /// Delete a setting
    async fn delete(&self, key: &str) -> Result<(), DomainError>;
}