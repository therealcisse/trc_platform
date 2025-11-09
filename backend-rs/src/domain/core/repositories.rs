//! Core repository traits

use async_trait::async_trait;
use crate::domain::DomainError;
use super::entities::RequestLog;

/// Request log repository trait
#[async_trait]
pub trait RequestLogRepository: Send + Sync {
    /// Save a request log entry
    async fn save(&self, log: &RequestLog) -> Result<(), DomainError>;

    /// Find request logs for a user with pagination
    async fn find_by_user(
        &self,
        user_id: &str,
        limit: u64,
        offset: u64,
    ) -> Result<Vec<RequestLog>, DomainError>;

    /// Count request logs for a user
    async fn count_by_user(&self, user_id: &str) -> Result<u64, DomainError>;

    /// Find request logs by date range
    async fn find_by_date_range(
        &self,
        start_date: chrono::DateTime<chrono::Utc>,
        end_date: chrono::DateTime<chrono::Utc>,
        limit: u64,
    ) -> Result<Vec<RequestLog>, DomainError>;

    /// Find request logs by status code
    async fn find_by_status_code(&self, status_code: u16, limit: u64) -> Result<Vec<RequestLog>, DomainError>;

    /// Delete old request logs (cleanup)
    async fn delete_old(&self, older_than: chrono::DateTime<chrono::Utc>) -> Result<u64, DomainError>;

    /// Get request statistics for a user in a date range
    async fn get_user_stats(
        &self,
        user_id: &str,
        start_date: chrono::DateTime<chrono::Utc>,
        end_date: chrono::DateTime<chrono::Utc>,
    ) -> Result<RequestStats, DomainError>;
}

/// Request statistics
#[derive(Debug, Clone)]
pub struct RequestStats {
    pub total_requests: u64,
    pub successful_requests: u64,
    pub failed_requests: u64,
    pub average_response_time: f64,
    pub total_response_bytes: u64,
}