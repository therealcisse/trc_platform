//! Repository implementations using SQLx

pub mod users;
pub mod api_tokens;
pub mod billing_periods;
pub mod request_logs;
pub mod invite_codes;
pub mod settings;

pub use users::*;
pub use api_tokens::*;
pub use billing_periods::*;
pub use request_logs::*;
pub use invite_codes::*;
pub use settings::*;

use sqlx::PgPool;
use std::sync::Arc;

/// Repository manager for dependency injection
#[derive(Clone)]
pub struct RepositoryManager {
    pool: Arc<PgPool>,
}

impl RepositoryManager {
    pub fn new(pool: Arc<PgPool>) -> Self {
        Self { pool }
    }

    pub fn users(&self) -> &crate::infrastructure::database::repositories::UserRepository {
        todo!("Implement UserRepository")
    }

    pub fn api_tokens(&self) -> &crate::infrastructure::database::repositories::ApiTokenRepository {
        todo!("Implement ApiTokenRepository")
    }

    pub fn billing_periods(&self) -> &crate::infrastructure::database::repositories::BillingPeriodRepository {
        todo!("Implement BillingPeriodRepository")
    }

    pub fn request_logs(&self) -> &crate::infrastructure::database::repositories::RequestLogRepository {
        todo!("Implement RequestLogRepository")
    }

    pub fn invite_codes(&self) -> &crate::infrastructure::database::repositories::InviteCodeRepository {
        todo!("Implement InviteCodeRepository")
    }

    pub fn settings(&self) -> &crate::infrastructure::database::repositories::SettingsRepository {
        todo!("Implement SettingsRepository")
    }

    /// Execute a transaction
    pub async fn transaction<F, R>(&self, f: F) -> Result<R, sqlx::Error>
    where
        F: FnOnce() -> Result<R, sqlx::Error>,
    {
        let mut tx = self.pool.begin().await?;
        let result = f()?;
        tx.commit().await?;
        Ok(result)
    }
}

/// Transaction manager for complex operations
pub struct TransactionManager<'a> {
    tx: &'a mut sqlx::Transaction<'a, sqlx::Postgres>,
}

impl<'a> TransactionManager<'a> {
    fn new(tx: &'a mut sqlx::Transaction<'a, sqlx::Postgres>) -> Self {
        Self { tx }
    }

    pub fn users(&mut self) -> &mut crate::infrastructure::database::repositories::UserRepository {
        todo!("Implement UserRepository for transactions")
    }

    pub fn api_tokens(&mut self) -> &mut crate::infrastructure::database::repositories::ApiTokenRepository {
        todo!("Implement ApiTokenRepository for transactions")
    }

    pub fn billing_periods(&mut self) -> &mut crate::infrastructure::database::repositories::BillingPeriodRepository {
        todo!("Implement BillingPeriodRepository for transactions")
    }
}