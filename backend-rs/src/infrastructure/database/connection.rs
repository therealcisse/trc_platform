//! Database connection management

use sqlx::{PgPool, postgres::PgPoolOptions};
use std::time::Duration;
use crate::config::settings::DatabaseSettings;
use crate::AppError;

/// Create database connection pool with optimized settings
pub async fn create_pool(settings: &DatabaseSettings) -> Result<sqlx::PgPool, AppError> {
    let pool = PgPoolOptions::new()
        .max_connections(settings.max_connections)
        .min_connections(settings.min_connections)
        .acquire_timeout(Duration::from_secs(settings.acquire_timeout_seconds))
        .idle_timeout(Duration::from_secs(settings.idle_timeout_seconds))
        .max_lifetime(Duration::from_secs(settings.max_lifetime_seconds))
        .test_before_acquire(true)
        .connect(&settings.url)
        .await
        .map_err(|e| AppError::Database(e.into()))?;

    // Test the connection with a simple query
    sqlx::query("SELECT 1")
        .fetch_one(&pool)
        .await
        .map_err(|e| AppError::Database(e))?;

    tracing::info!("Database connection pool created successfully");
    Ok(pool)
}

/// Run database migrations
pub async fn run_migrations(pool: &sqlx::PgPool) -> Result<(), AppError> {
    sqlx::migrate!("./migrations")
        .run(pool)
        .await
        .map_err(|e| AppError::Database(e.into()))?;

    tracing::info!("Database migrations completed successfully");
    Ok(())
}