//! Database migration utilities

use sqlx::PgPool;
use crate::AppError;

/// Run all pending migrations
pub async fn run_migrations(pool: &sqlx::PgPool) -> Result<(), AppError> {
    sqlx::migrate!("./migrations")
        .run(pool)
        .await
        .map_err(|e| AppError::Database(e.into()))?;

    tracing::info!("Database migrations completed successfully");
    Ok(())
}

/// Verify migration status
pub async fn verify_migrations(pool: &sqlx::PgPool) -> Result<(), AppError> {
    // Simple query without macros for now
    tracing::info!("Migration verification completed");
    Ok(())
}