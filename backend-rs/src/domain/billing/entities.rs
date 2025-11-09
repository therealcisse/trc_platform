//! Billing domain entities

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc, NaiveDate};
use uuid::Uuid;
use crate::domain::DomainError;

/// Billing period aggregate root
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BillingPeriod {
    id: Uuid,
    user_id: Uuid,
    period_start: NaiveDate,
    period_end: NaiveDate,
    total_requests: i32,
    total_cost_cents: i32,
    is_current: bool,
    payment_status: PaymentStatus,
    version: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PaymentStatus {
    Pending,
    Paid,
    Overdue,
    Waived,
}

impl BillingPeriod {
    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn total_requests(&self) -> i32 {
        self.total_requests
    }

    pub fn total_cost_cents(&self) -> i32 {
        self.total_cost_cents
    }

    pub fn is_current(&self) -> bool {
        self.is_current
    }
}

/// Subscription aggregate root
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subscription {
    id: Uuid,
    user_id: Uuid,
    stripe_subscription_id: Option<String>,
    tier: SubscriptionTier,
    status: SubscriptionStatus,
    current_period_start: Option<DateTime<Utc>>,
    current_period_end: Option<DateTime<Utc>>,
    cancel_at_period_end: bool,
    created_at: DateTime<Utc>,
    updated_at: DateTime<Utc>,
    version: i64,
}

/// Subscription tier enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SubscriptionTier {
    Free,
    Basic,
    Pro,
    Enterprise,
}

/// Subscription status enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SubscriptionStatus {
    Active,
    Cancelled,
    Expired,
    Trial,
}

impl Subscription {
    pub fn new(
        user_id: Uuid,
        tier: SubscriptionTier,
        stripe_subscription_id: Option<String>,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            user_id,
            stripe_subscription_id,
            tier,
            status: SubscriptionStatus::Active,
            current_period_start: Some(Utc::now()),
            current_period_end: Some(Utc::now() + chrono::Duration::days(30)),
            cancel_at_period_end: false,
            created_at: Utc::now(),
            updated_at: Utc::now(),
            version: 1,
        }
    }

    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn user_id(&self) -> Uuid {
        self.user_id
    }

    pub fn tier(&self) -> &SubscriptionTier {
        &self.tier
    }

    pub fn status(&self) -> &SubscriptionStatus {
        &self.status
    }

    pub fn is_active(&self) -> bool {
        matches!(self.status, SubscriptionStatus::Active)
    }

    pub fn cancel(&mut self) {
        self.status = SubscriptionStatus::Cancelled;
        self.cancel_at_period_end = true;
        self.updated_at = Utc::now();
    }

    pub fn update_period(&mut self, start: DateTime<Utc>, end: DateTime<Utc>) {
        self.current_period_start = Some(start);
        self.current_period_end = Some(end);
        self.updated_at = Utc::now();
    }
}