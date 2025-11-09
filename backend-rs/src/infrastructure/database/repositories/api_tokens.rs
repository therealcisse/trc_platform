//! API token repository implementation

use async_trait::async_trait;
use sqlx::PgPool;
use std::sync::Arc;

use crate::domain::users::entities::ApiToken;
use crate::domain::users::repositories::ApiTokenRepository;

/// PostgreSQL implementation of ApiTokenRepository
pub struct PostgresApiTokenRepository {
    pool: Arc<PgPool>,
}

impl PostgresApiTokenRepository {
    pub fn new(pool: Arc<PgPool>) -> Self {
        Self { pool }
    }
}

#[async_trait]
impl ApiTokenRepository for PostgresApiTokenRepository {
    async fn find_by_token(&self, token: &str) -> Result<Option<ApiToken>, crate::domain::DomainError> {
        // TODO: Implement token lookup
        tracing::info!("Finding API token: {}", token);
        Ok(None)
    }

    async fn save(&self, token: &ApiToken) -> Result<(), crate::domain::DomainError> {
        // TODO: Implement token saving
        tracing::info!("Saving API token: {:?}", token);
        Ok(())
    }

    async fn revoke(&self, token_id: &str) -> Result<(), crate::domain::DomainError> {
        // TODO: Implement token revocation
        tracing::info!("Revoking API token: {}", token_id);
        Ok(())
    }
}