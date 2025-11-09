//! Billing repository traits

use async_trait::async_trait;
use crate::domain::DomainError;
use super::entities::{BillingPeriod, Subscription};

/// Billing period repository trait
#[async_trait]
pub trait BillingPeriodRepository: Send + Sync {
    /// Find a billing period by its ID
    async fn find_by_id(&self, id: &str) -> Result<Option<BillingPeriod>, DomainError>;

    /// Find the active billing period for a user
    async fn find_active_for_user(&self, user_id: &str) -> Result<Option<BillingPeriod>, DomainError>;

    /// Save a billing period (create or update)
    async fn save(&self, period: &BillingPeriod) -> Result<(), DomainError>;

    /// Find billing periods for a user within a date range
    async fn find_for_user_in_range(
        &self,
        user_id: &str,
        start_date: chrono::NaiveDate,
        end_date: chrono::NaiveDate,
    ) -> Result<Vec<BillingPeriod>, DomainError>;

    /// Count billing periods for a user
    async fn count_for_user(&self, user_id: &str) -> Result<u64, DomainError>;
}

/// Subscription repository trait
#[async_trait]
pub trait SubscriptionRepository: Send + Sync {
    /// Find a subscription by its ID
    async fn find_by_id(&self, id: &str) -> Result<Option<Subscription>, DomainError>;

    /// Find the active subscription for a user
    async fn find_active_for_user(&self, user_id: &str) -> Result<Option<Subscription>, DomainError>;

    /// Save a subscription (create or update)
    async fn save(&self, subscription: &Subscription) -> Result<(), DomainError>;

    /// Find subscriptions by status
    async fn find_by_status(&self, status: &str) -> Result<Vec<Subscription>, DomainError>;

    /// Find subscriptions that will expire soon
    async fn find_expiring_soon(&self, days_ahead: u32) -> Result<Vec<Subscription>, DomainError>;

    /// Cancel a subscription
    async fn cancel(&self, subscription_id: &str) -> Result<(), DomainError>;
}