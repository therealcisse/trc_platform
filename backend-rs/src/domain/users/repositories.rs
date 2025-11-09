//! User repository traits

use async_trait::async_trait;
use crate::domain::DomainError;
use super::entities::{User, ApiToken};

/// User repository trait
#[async_trait]
pub trait UserRepository: Send + Sync {
    /// Find a user by their ID
    async fn find_by_id(&self, id: &str) -> Result<Option<User>, DomainError>;

    /// Find a user by their email address
    async fn find_by_email(&self, email: &str) -> Result<Option<User>, DomainError>;

    /// Save a user (create or update)
    async fn save(&self, user: &User) -> Result<(), DomainError>;

    /// Delete a user by their ID
    async fn delete(&self, id: &str) -> Result<(), DomainError>;

    /// Find all active users with pagination
    async fn find_active(&self, limit: u64, offset: u64) -> Result<Vec<User>, DomainError>;

    /// Count total active users
    async fn count_active(&self) -> Result<u64, DomainError>;
}

/// API Token repository trait
#[async_trait]
pub trait ApiTokenRepository: Send + Sync {
    /// Find a token by its hash
    async fn find_by_token(&self, token: &str) -> Result<Option<ApiToken>, DomainError>;

    /// Find all tokens for a user
    async fn find_by_user(&self, user_id: &str) -> Result<Vec<ApiToken>, DomainError>;

    /// Save a token (create or update)
    async fn save(&self, token: &ApiToken) -> Result<(), DomainError>;

    /// Revoke a token by its ID
    async fn revoke(&self, token_id: &str) -> Result<(), DomainError>;

    /// Delete expired tokens
    async fn delete_expired(&self) -> Result<u64, DomainError>;

    /// Update last used timestamp for a token
    async fn update_last_used(&self, token_id: &str) -> Result<(), DomainError>;
}