//! Database layer with SQLx integration

pub mod connection;
pub mod models;
pub mod repositories;
pub mod migrations;

pub use connection::*;
pub use models::*;
pub use repositories::*;
pub use migrations::*;

use sqlx::PgPool;
use std::sync::Arc;

/// Database connection pool wrapper
#[derive(Clone)]
pub struct Database {
    pool: Arc<PgPool>,
}

impl Database {
    pub fn new(pool: PgPool) -> Self {
        Self {
            pool: Arc::new(pool),
        }
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }

    /// Health check for database connectivity
    pub async fn health_check(&self) -> Result<(), sqlx::Error> {
        sqlx::query("SELECT 1")
            .fetch_one(self.pool.as_ref())
            .await?;
        Ok(())
    }
}