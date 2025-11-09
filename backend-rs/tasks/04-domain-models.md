# Task 4: Domain Models and Business Logic

## Description
Implement the core domain entities and business logic following Clean Architecture principles. This task creates the domain layer with proper encapsulation, validation, and business rules that are independent of infrastructure concerns.

## Acceptance Criteria
1. ✅ Create domain entities for all business concepts (User, ApiToken, BillingPeriod, etc.)
2. ✅ Implement domain-specific business logic and validation rules
3. ✅ Use value objects for domain concepts (Email, Money, etc.)
4. ✅ Implement domain events for important business operations
5. ✅ Create domain services for complex business logic
6. ✅ Add proper error handling with domain-specific errors
7. ✅ Test domain logic independently of infrastructure

## Prerequisites
- **Task 1**: Project Setup (completed)
- **Task 3**: Configuration (completed - for domain validation)

## Technical Implementation

### Step 1: Create Domain Foundation

#### src/domain/mod.rs
```rust
//! Domain layer - Business entities and logic

pub mod users;
pub mod billing;
pub mod core;
pub mod admin;
pub mod shared;

use thiserror::Error;

/// Domain-specific errors
#[derive(Debug, Error)]
pub enum DomainError {
    #[error("Validation error: {field} - {message}")]
    ValidationError { field: String, message: String },

    #[error("Business rule violation: {rule}")]
    BusinessRuleViolation { rule: String },

    #[error("Entity not found: {entity} with id {id}")]
    NotFound { entity: String, id: String },

    #[error("Duplicate entity: {entity} with value {value}")]
    Duplicate { entity: String, value: String },

    #[error("Access denied: {reason}")]
    AccessDenied { reason: String },

    #[error("Operation not allowed: {operation}")]
    OperationNotAllowed { operation: String },
}

/// Domain events for important business operations
#[derive(Debug, Clone)]
pub enum DomainEvent {
    UserRegistered { user_id: String, email: String },
    UserVerified { user_id: String, email: String },
    ApiTokenCreated { user_id: String, token_id: String },
    ApiTokenRevoked { user_id: String, token_id: String },
    BillingPeriodCreated { user_id: String, period_id: String },
    RequestProcessed { user_id: String, request_id: String, cost_cents: i32 },
    PaymentProcessed { period_id: String, amount_cents: i32 },
}

pub type DomainResult<T> = Result<T, DomainError>;
```

#### src/domain/shared/mod.rs
```rust
//! Shared domain value objects and utilities

pub mod value_objects;
pub mod events;

pub use value_objects::*;
pub use events::*;
```

#### src/domain/shared/value_objects.rs
```rust
//! Shared value objects for the domain

use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Email value object with validation
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Email(String);

impl Email {
    pub fn new(email: &str) -> DomainResult<Self> {
        let email = email.trim().to_lowercase();

        // Basic email validation
        if email.is_empty() {
            return Err(DomainError::ValidationError {
                field: "email".to_string(),
                message: "Email cannot be empty".to_string(),
            });
        }

        if !email.contains('@') || !email.contains('.') {
            return Err(DomainError::ValidationError {
                field: "email".to_string(),
                message: "Invalid email format".to_string(),
            });
        }

        if email.len() > 255 {
            return Err(DomainError::ValidationError {
                field: "email".to_string(),
                message: "Email too long (max 255 characters)".to_string(),
            });
        }

        Ok(Email(email))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn into_string(self) -> String {
        self.0
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Money value object for financial calculations
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Money {
    amount_cents: i64,
}

impl Money {
    pub fn new_cents(cents: i64) -> DomainResult<Self> {
        if cents < 0 {
            return Err(DomainError::ValidationError {
                field: "amount".to_string(),
                message: "Amount cannot be negative".to_string(),
            });
        }

        if cents > i64::MAX / 100 {
            return Err(DomainError::ValidationError {
                field: "amount".to_string(),
                message: "Amount too large".to_string(),
            });
        }

        Ok(Money { amount_cents: cents })
    }

    pub fn from_dollars(dollars: f64) -> DomainResult<Self> {
        let cents = (dollars * 100.0).round() as i64;
        Self::new_cents(cents)
    }

    pub fn cents(&self) -> i64 {
        self.amount_cents
    }

    pub fn dollars(&self) -> f64 {
        self.amount_cents as f64 / 100.0
    }

    pub fn add(&self, other: Money) -> DomainResult<Money> {
        let result = self.amount_cents.checked_add(other.amount_cents)
            .ok_or_else(|| DomainError::ValidationError {
                field: "amount".to_string(),
                message: "Addition overflow".to_string(),
            })?;
        Ok(Money { amount_cents: result })
    }

    pub fn multiply(&self, factor: i32) -> DomainResult<Money> {
        let result = self.amount_cents.checked_mul(factor as i64)
            .ok_or_else(|| DomainError::ValidationError {
                field: "amount".to_string(),
                message: "Multiplication overflow".to_string(),
            })?;
        Ok(Money { amount_cents: result })
    }
}

impl fmt::Display for Money {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "${:.2}", self.dollars())
    }
}

/// Token prefix value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TokenPrefix(String);

impl TokenPrefix {
    pub fn new(prefix: &str) -> DomainResult<Self> {
        let prefix = prefix.trim();

        if prefix.is_empty() {
            return Err(DomainError::ValidationError {
                field: "token_prefix".to_string(),
                message: "Token prefix cannot be empty".to_string(),
            });
        }

        if prefix.len() > 64 {
            return Err(DomainError::ValidationError {
                field: "token_prefix".to_string(),
                message: "Token prefix too long (max 64 characters)".to_string(),
            });
        }

        Ok(TokenPrefix(prefix.to_string()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Invite code value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct InviteCode(String);

impl InviteCode {
    pub fn new(code: &str) -> DomainResult<Self> {
        let code = code.trim().to_uppercase();

        if code.is_empty() {
            return Err(DomainError::ValidationError {
                field: "invite_code".to_string(),
                message: "Invite code cannot be empty".to_string(),
            });
        }

        if code.len() < 6 || code.len() > 32 {
            return Err(DomainError::ValidationError {
                field: "invite_code".to_string(),
                message: "Invite code must be 6-32 characters".to_string(),
            });
        }

        // Only allow alphanumeric characters
        if !code.chars().all(|c| c.is_alphanumeric()) {
            return Err(DomainError::ValidationError {
                field: "invite_code".to_string(),
                message: "Invite code can only contain alphanumeric characters".to_string(),
            });
        }

        Ok(InviteCode(code))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn into_string(self) -> String {
        self.0
    }
}

impl fmt::Display for InviteCode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Period range value object for billing periods
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PeriodRange {
    start: chrono::NaiveDate,
    end: chrono::NaiveDate,
}

impl PeriodRange {
    pub fn new(start: chrono::NaiveDate, end: chrono::NaiveDate) -> DomainResult<Self> {
        if start > end {
            return Err(DomainError::ValidationError {
                field: "period_range".to_string(),
                message: "Start date cannot be after end date".to_string(),
            });
        }

        Ok(PeriodRange { start, end })
    }

    pub fn monthly(year: i32, month: u32) -> DomainResult<Self> {
        let start = chrono::NaiveDate::from_ymd_opt(year, month, 1)
            .ok_or_else(|| DomainError::ValidationError {
                field: "period_range".to_string(),
                message: "Invalid year/month".to_string(),
            })?;

        let end = start + chrono::Duration::days(-1) + chrono::Duration::days(1); // End of month

        // Get the last day of the month
        let next_month = if month == 12 {
            chrono::NaiveDate::from_ymd_opt(year + 1, 1, 1)
        } else {
            chrono::NaiveDate::from_ymd_opt(year, month + 1, 1)
        }.ok_or_else(|| DomainError::ValidationError {
            field: "period_range".to_string(),
            message: "Invalid date calculation".to_string(),
        })?;

        let end = next_month - chrono::Duration::days(1);

        Ok(PeriodRange { start, end })
    }

    pub fn start(&self) -> chrono::NaiveDate {
        self.start
    }

    pub fn end(&self) -> chrono::NaiveDate {
        self.end
    }

    pub fn contains(&self, date: chrono::NaiveDate) -> bool {
        date >= self.start && date <= self.end
    }

    pub fn days(&self) -> i64 {
        (self.end - self.start).num_days() + 1
    }
}

/// Request status enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum RequestStatus {
    Success,
    Error,
}

/// Payment status enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PaymentStatus {
    Pending,
    Paid,
    Overdue,
    Waived,
}

impl PaymentStatus {
    pub fn is_paid(&self) -> bool {
        matches!(self, PaymentStatus::Paid)
    }

    pub fn can_transition_to(&self, new_status: &PaymentStatus) -> bool {
        use PaymentStatus::*;

        match (self, new_status) {
            (Pending, Paid) => true,
            (Pending, Overdue) => true,
            (Pending, Waived) => true,
            (Overdue, Paid) => true,
            (Overdue, Waived) => true,
            _ => false,
        }
    }
}
```

#### src/domain/shared/events.rs
```rust
//! Domain events and event handling

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Base trait for domain events
pub trait DomainEvent {
    fn event_id(&self) -> Uuid;
    fn occurred_at(&self) -> DateTime<Utc>;
    fn event_type(&self) -> &'static str;
}

/// User registered event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserRegisteredEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub email: String,
}

impl DomainEvent for UserRegisteredEvent {
    fn event_id(&self) -> Uuid {
        self.event_id
    }

    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "UserRegistered"
    }
}

/// User verified event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserVerifiedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub email: String,
}

impl DomainEvent for UserVerifiedEvent {
    fn event_id(&self) -> Uuid {
        self.event_id
    }

    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "UserVerified"
    }
}

/// API token created event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiTokenCreatedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub token_id: Uuid,
    pub token_name: String,
}

impl DomainEvent for ApiTokenCreatedEvent {
    fn event_id(&self) -> Uuid {
        self.event_id
    }

    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "ApiTokenCreated"
    }
}

/// Request processed event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RequestProcessedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub request_id: Uuid,
    pub service: String,
    pub status: crate::domain::shared::RequestStatus,
    pub cost_cents: i32,
    pub duration_ms: i32,
}

impl DomainEvent for RequestProcessedEvent {
    fn event_id(&self) -> Uuid {
        self.event_id
    }

    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "RequestProcessed"
    }
}

/// Billing period created event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BillingPeriodCreatedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub period_id: Uuid,
    pub period_start: chrono::NaiveDate,
    pub period_end: chrono::NaiveDate,
}

impl DomainEvent for BillingPeriodCreatedEvent {
    fn event_id(&self) -> Uuid {
        self.event_id
    }

    fn occurred_at(&self) -> DateTime<Utc> {
        self.occurred_at
    }

    fn event_type(&self) -> &'static str {
        "BillingPeriodCreated"
    }
}
```

### Step 2: User Domain

#### src/domain/users/mod.rs
```rust
//! User domain entities and business logic

pub mod entities;
pub mod value_objects;
pub mod services;
pub mod events;

pub use entities::*;
pub use value_objects::*;
pub use services::*;
pub use events::*;
```

#### src/domain/users/entities.rs
```rust
//! User domain entity

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use crate::domain::shared::{Email, DomainError, DomainResult};
use super::{PasswordHash, UserProfile};

/// User aggregate root
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    id: Uuid,
    email: Email,
    password_hash: PasswordHash,
    is_active: bool,
    is_staff: bool,
    email_verified_at: Option<DateTime<Utc>>,
    date_joined: DateTime<Utc>,
    profile: UserProfile,
    version: i64,
}

impl User {
    /// Create a new user
    pub fn create(
        email: Email,
        password_hash: PasswordHash,
        profile: UserProfile,
    ) -> DomainResult<User> {
        let user = User {
            id: Uuid::new_v4(),
            email,
            password_hash,
            is_active: true,
            is_staff: false,
            email_verified_at: None,
            date_joined: Utc::now(),
            profile,
            version: 1,
        };

        Ok(user)
    }

    /// Verify user's email
    pub fn verify_email(&mut self) -> DomainResult<UserVerifiedEvent> {
        if self.email_verified_at.is_some() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Email is already verified".to_string(),
            });
        }

        self.email_verified_at = Some(Utc::now());
        self.version += 1;

        Ok(UserVerifiedEvent {
            event_id: Uuid::new_v4(),
            occurred_at: Utc::now(),
            user_id: self.id,
            email: self.email.as_str().to_string(),
        })
    }

    /// Deactivate user
    pub fn deactivate(&mut self) -> DomainResult<()> {
        if !self.is_active {
            return Err(DomainError::BusinessRuleViolation {
                rule: "User is already inactive".to_string(),
            });
        }

        self.is_active = false;
        self.version += 1;
        Ok(())
    }

    /// Activate user
    pub fn activate(&mut self) -> DomainResult<()> {
        if self.is_active {
            return Err(DomainError::BusinessRuleViolation {
                rule: "User is already active".to_string(),
            });
        }

        self.is_active = true;
        self.version += 1;
        Ok(())
    }

    /// Promote to staff
    pub fn promote_to_staff(&mut self) -> DomainResult<()> {
        if self.is_staff {
            return Err(DomainError::BusinessRuleViolation {
                rule: "User is already staff".to_string(),
            });
        }

        self.is_staff = true;
        self.version += 1;
        Ok(())
    }

    /// Update password
    pub fn update_password(&mut self, new_password_hash: PasswordHash) -> DomainResult<()> {
        self.password_hash = new_password_hash;
        self.version += 1;
        Ok(())
    }

    /// Update profile
    pub fn update_profile(&mut self, profile: UserProfile) -> DomainResult<()> {
        self.profile = profile;
        self.version += 1;
        Ok(())
    }

    // Getters
    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn email(&self) -> &Email {
        &self.email
    }

    pub fn password_hash(&self) -> &PasswordHash {
        &self.password_hash
    }

    pub fn is_active(&self) -> bool {
        self.is_active
    }

    pub fn is_staff(&self) -> bool {
        self.is_staff
    }

    pub fn is_email_verified(&self) -> bool {
        self.email_verified_at.is_some()
    }

    pub fn email_verified_at(&self) -> Option<DateTime<Utc>> {
        self.email_verified_at
    }

    pub fn date_joined(&self) -> DateTime<Utc> {
        self.date_joined
    }

    pub fn profile(&self) -> &UserProfile {
        &self.profile
    }

    pub fn version(&self) -> i64 {
        self.version
    }

    /// Check if user can access a resource
    pub fn can_access(&self, resource_type: &str) -> bool {
        if !self.is_active {
            return false;
        }

        match resource_type {
            "admin" => self.is_staff,
            "user" => true,
            _ => false,
        }
    }

    /// Validate user for login
    pub fn validate_for_login(&self) -> DomainResult<()> {
        if !self.is_active {
            return Err(DomainError::AccessDenied {
                reason: "User account is inactive".to_string(),
            });
        }

        Ok(())
    }

    /// Validate user for API access
    pub fn validate_for_api_access(&self) -> DomainResult<()> {
        self.validate_for_login()?;

        if !self.is_email_verified() {
            return Err(DomainError::AccessDenied {
                reason: "Email address not verified".to_string(),
            });
        }

        if !self.profile.has_accepted_terms() {
            return Err(DomainError::AccessDenied {
                reason: "Terms of service not accepted".to_string(),
            });
        }

        if !self.profile.has_acknowledged_disclaimer() {
            return Err(DomainError::AccessDenied {
                reason: "Disclaimer not acknowledged".to_string(),
            });
        }

        Ok(())
    }
}

impl PartialEq for User {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}

impl Eq for User {}
```

#### src/domain/users/value_objects.rs
```rust
//! User domain value objects

use serde::{Deserialize, Serialize};
use crate::domain::shared::{DomainError, DomainResult};

/// Password hash value object
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PasswordHash(String);

impl PasswordHash {
    pub fn new(hash: &str) -> DomainResult<Self> {
        let hash = hash.trim();

        if hash.is_empty() {
            return Err(DomainError::ValidationError {
                field: "password_hash".to_string(),
                message: "Password hash cannot be empty".to_string(),
            });
        }

        if hash.len() > 255 {
            return Err(DomainError::ValidationError {
                field: "password_hash".to_string(),
                message: "Password hash too long (max 255 characters)".to_string(),
            });
        }

        // Basic validation for Argon2 hash format
        if !hash.starts_with("$argon2") {
            return Err(DomainError::ValidationError {
                field: "password_hash".to_string(),
                message: "Invalid password hash format".to_string(),
            });
        }

        Ok(PasswordHash(hash.to_string()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn into_string(self) -> String {
        self.0
    }
}

/// User profile value object
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UserProfile {
    pub user_accepted_terms: bool,
    pub user_acknowledged_disclaimer: bool,
}

impl UserProfile {
    pub fn new(
        accepted_terms: bool,
        acknowledged_disclaimer: bool,
    ) -> DomainResult<Self> {
        Ok(UserProfile {
            user_accepted_terms: accepted_terms,
            user_acknowledged_disclaimer: acknowledged_disclaimer,
        })
    }

    pub fn has_accepted_terms(&self) -> bool {
        self.user_accepted_terms
    }

    pub fn has_acknowledged_disclaimer(&self) -> bool {
        self.user_acknowledged_disclaimer
    }

    pub fn accept_terms(&mut self) {
        self.user_accepted_terms = true;
    }

    pub fn acknowledge_disclaimer(&mut self) {
        self.user_acknowledged_disclaimer = true;
    }
}

impl Default for UserProfile {
    fn default() -> Self {
        UserProfile {
            user_accepted_terms: false,
            user_acknowledged_disclaimer: false,
        }
    }
}

/// Password requirements
pub struct PasswordRequirements;

impl PasswordRequirements {
    pub fn validate(password: &str) -> DomainResult<()> {
        if password.len() < 8 {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must be at least 8 characters".to_string(),
            });
        }

        if password.len() > 128 {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password too long (max 128 characters)".to_string(),
            });
        }

        // Check for at least one letter
        if !password.chars().any(|c| c.is_alphabetic()) {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must contain at least one letter".to_string(),
            });
        }

        // Check for at least one number
        if !password.chars().any(|c| c.is_numeric()) {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must contain at least one number".to_string(),
            });
        }

        Ok(())
    }
}
```

#### src/domain/users/services.rs
```rust
//! User domain services

use crate::domain::shared::{Email, PasswordHash, UserProfile, DomainError, DomainResult};
use super::User;

/// User domain service for complex business logic
pub struct UserDomainService;

impl UserDomainService {
    /// Validate user registration data
    pub fn validate_registration(
        email: Email,
        password: &str,
        profile: UserProfile,
    ) -> DomainResult<()> {
        // Validate password requirements
        PasswordRequirements::validate(password)?;

        // Validate profile requirements
        if !profile.has_accepted_terms() {
            return Err(DomainError::ValidationError {
                field: "user_accepted_terms".to_string(),
                message: "Terms of service must be accepted".to_string(),
            });
        }

        if !profile.has_acknowledged_disclaimer() {
            return Err(DomainError::ValidationError {
                field: "user_acknowledged_disclaimer".to_string(),
                message: "Disclaimer must be acknowledged".to_string(),
            });
        }

        Ok(())
    }

    /// Check if email is allowed for registration
    pub fn is_email_allowed(email: &Email) -> DomainResult<()> {
        // Add business rules for email restrictions if needed
        // For example, block certain domains, require specific format, etc.

        let email_str = email.as_str();

        // Example: Block temporary email domains
        let blocked_domains = vec![
            "tempmail.com",
            "10minutemail.com",
            "guerrillamail.com",
        ];

        if let Some(domain) = email_str.split('@').nth(1) {
            if blocked_domains.contains(&domain) {
                return Err(DomainError::ValidationError {
                    field: "email".to_string(),
                    message: "Temporary email addresses are not allowed".to_string(),
                });
            }
        }

        Ok(())
    }
}

/// Password requirements validation
pub struct PasswordRequirements;

impl PasswordRequirements {
    pub fn validate(password: &str) -> DomainResult<()> {
        if password.len() < 8 {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must be at least 8 characters".to_string(),
            });
        }

        if password.len() > 128 {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password too long (max 128 characters)".to_string(),
            });
        }

        // Check for at least one letter
        if !password.chars().any(|c| c.is_alphabetic()) {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must contain at least one letter".to_string(),
            });
        }

        // Check for at least one number
        if !password.chars().any(|c| c.is_numeric()) {
            return Err(DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must contain at least one number".to_string(),
            });
        }

        Ok(())
    }
}
```

#### src/domain/users/events.rs
```rust
//! User domain events

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// User registered event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserRegisteredEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub email: String,
}

impl UserRegisteredEvent {
    pub fn new(user_id: Uuid, email: String) -> Self {
        Self {
            event_id: Uuid::new_v4(),
            occurred_at: Utc::now(),
            user_id,
            email,
        }
    }
}

/// User verified event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserVerifiedEvent {
    pub event_id: Uuid,
    pub occurred_at: DateTime<Utc>,
    pub user_id: Uuid,
    pub email: String,
}

impl UserVerifiedEvent {
    pub fn new(user_id: Uuid, email: String) -> Self {
        Self {
            event_id: Uuid::new_v4(),
            occurred_at: Utc::now(),
            user_id,
            email,
        }
    }
}
```

### Step 3: API Token Domain

#### src/domain/users/entities.rs (add to existing file)
```rust
// Add these structures to the existing entities.rs file

/// API Token entity
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiToken {
    id: Uuid,
    user_id: Uuid,
    token_hash: String,
    token_prefix: crate::domain::shared::TokenPrefix,
    name: String,
    created_at: DateTime<Utc>,
    last_used_at: Option<DateTime<Utc>>,
    expires_at: Option<DateTime<Utc>>,
    revoked_at: Option<DateTime<Utc>>,
}

impl ApiToken {
    /// Create a new API token
    pub fn create(
        user_id: Uuid,
        token_hash: String,
        token_prefix: crate::domain::shared::TokenPrefix,
        name: String,
        expires_at: Option<DateTime<Utc>>,
    ) -> DomainResult<Self> {
        if name.trim().is_empty() {
            return Err(DomainError::ValidationError {
                field: "name".to_string(),
                message: "Token name cannot be empty".to_string(),
            });
        }

        if name.len() > 255 {
            return Err(DomainError::ValidationError {
                field: "name".to_string(),
                message: "Token name too long (max 255 characters)".to_string(),
            });
        }

        Ok(ApiToken {
            id: Uuid::new_v4(),
            user_id,
            token_hash,
            token_prefix,
            name,
            created_at: Utc::now(),
            last_used_at: None,
            expires_at,
            revoked_at: None,
        })
    }

    /// Revoke the token
    pub fn revoke(&mut self) -> DomainResult<()> {
        if self.revoked_at.is_some() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Token is already revoked".to_string(),
            });
        }

        self.revoked_at = Some(Utc::now());
        Ok(())
    }

    /// Update last used timestamp
    pub fn update_last_used(&mut self) -> DomainResult<()> {
        if !self.is_valid() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Cannot update last used for invalid token".to_string(),
            });
        }

        self.last_used_at = Some(Utc::now());
        Ok(())
    }

    /// Check if token is valid for use
    pub fn is_valid(&self) -> bool {
        let now = Utc::now();

        // Check if revoked
        if let Some(revoked_at) = self.revoked_at {
            if revoked_at <= now {
                return false;
            }
        }

        // Check if expired
        if let Some(expires_at) = self.expires_at {
            if expires_at <= now {
                return false;
            }
        }

        true
    }

    /// Check if token is expired
    pub fn is_expired(&self) -> bool {
        if let Some(expires_at) = self.expires_at {
            expires_at <= Utc::now()
        } else {
            false
        }
    }

    /// Check if token is revoked
    pub fn is_revoked(&self) -> bool {
        self.revoked_at.is_some()
    }

    // Getters
    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn user_id(&self) -> Uuid {
        self.user_id
    }

    pub fn token_hash(&self) -> &str {
        &self.token_hash
    }

    pub fn token_prefix(&self) -> &crate::domain::shared::TokenPrefix {
        &self.token_prefix
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn created_at(&self) -> DateTime<Utc> {
        self.created_at
    }

    pub fn last_used_at(&self) -> Option<DateTime<Utc>> {
        self.last_used_at
    }

    pub fn expires_at(&self) -> Option<DateTime<Utc>> {
        self.expires_at
    }

    pub fn revoked_at(&self) -> Option<DateTime<Utc>> {
        self.revoked_at
    }
}

impl PartialEq for ApiToken {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}

impl Eq for ApiToken {}
```

### Step 4: Billing Domain

#### src/domain/billing/mod.rs
```rust
//! Billing domain entities and business logic

pub mod entities;
pub mod value_objects;
pub mod services;
pub mod events;

pub use entities::*;
pub use value_objects::*;
pub use services::*;
pub use events::*;
```

#### src/domain/billing/entities.rs
```rust
//! Billing domain entities

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc, NaiveDate};
use uuid::Uuid;
use crate::domain::shared::{Money, PeriodRange, PaymentStatus, DomainError, DomainResult};

/// Billing period aggregate root
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BillingPeriod {
    id: Uuid,
    user_id: Uuid,
    period_range: PeriodRange,
    total_requests: i32,
    total_cost: Money,
    is_current: bool,
    payment_status: PaymentStatus,
    paid_at: Option<DateTime<Utc>>,
    paid_amount: Option<Money>,
    payment_reference: Option<String>,
    notes: Option<String>,
    version: i64,
}

impl BillingPeriod {
    /// Create a new billing period
    pub fn create(
        user_id: Uuid,
        period_range: PeriodRange,
        cost_per_request: Money,
    ) -> DomainResult<Self> {
        Ok(BillingPeriod {
            id: Uuid::new_v4(),
            user_id,
            period_range,
            total_requests: 0,
            total_cost: Money::new_cents(0)?,
            is_current: true,
            payment_status: PaymentStatus::Pending,
            paid_at: None,
            paid_amount: None,
            payment_reference: None,
            notes: None,
            version: 1,
        })
    }

    /// Add a successful request to the billing period
    pub fn add_request(&mut self, cost_per_request: Money) -> DomainResult<()> {
        if !self.is_current {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Cannot add requests to non-current billing period".to_string(),
            });
        }

        self.total_requests += 1;
        self.total_cost = self.total_cost.add(cost_per_request)?;
        self.version += 1;

        Ok(())
    }

    /// Process payment
    pub fn process_payment(
        &mut self,
        amount: Money,
        payment_reference: Option<String>,
    ) -> DomainResult<BillingPeriodPaidEvent> {
        if self.payment_status.is_paid() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Billing period is already paid".to_string(),
            });
        }

        if !self.payment_status.can_transition_to(&PaymentStatus::Paid) {
            return Err(DomainError::BusinessRuleViolation {
                rule: format!("Cannot transition from {:?} to Paid", self.payment_status),
            });
        }

        if amount.cents() != self.total_cost.cents() {
            return Err(DomainError::ValidationError {
                field: "amount".to_string(),
                message: format!(
                    "Payment amount {} does not match total cost {}",
                    amount,
                    self.total_cost
                ),
            });
        }

        self.payment_status = PaymentStatus::Paid;
        self.paid_at = Some(Utc::now());
        self.paid_amount = Some(amount);
        self.payment_reference = payment_reference;
        self.version += 1;

        Ok(BillingPeriodPaidEvent {
            event_id: Uuid::new_v4(),
            occurred_at: Utc::now(),
            period_id: self.id,
            user_id: self.user_id,
            amount_cents: amount.cents(),
            payment_reference,
        })
    }

    /// Mark as overdue
    pub fn mark_as_overdue(&mut self) -> DomainResult<()> {
        if self.payment_status.is_paid() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Cannot mark paid billing period as overdue".to_string(),
            });
        }

        if !self.payment_status.can_transition_to(&PaymentStatus::Overdue) {
            return Err(DomainError::BusinessRuleViolation {
                rule: format!("Cannot transition from {:?} to Overdue", self.payment_status),
            });
        }

        self.payment_status = PaymentStatus::Overdue;
        self.version += 1;
        Ok(())
    }

    /// Waive payment
    pub fn waive_payment(&mut self, reason: String) -> DomainResult<()> {
        if self.payment_status.is_paid() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Cannot waive payment for paid billing period".to_string(),
            });
        }

        if !self.payment_status.can_transition_to(&PaymentStatus::Waived) {
            return Err(DomainError::BusinessRuleViolation {
                rule: format!("Cannot transition from {:?} to Waived", self.payment_status),
            });
        }

        self.payment_status = PaymentStatus::Waived;
        self.notes = Some(reason);
        self.version += 1;
        Ok(())
    }

    /// Close the period (no longer current)
    pub fn close(&mut self) -> DomainResult<()> {
        if !self.is_current {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Billing period is already closed".to_string(),
            });
        }

        self.is_current = false;
        self.version += 1;
        Ok(())
    }

    /// Reopen the period (make current again)
    pub fn reopen(&mut self) -> DomainResult<()> {
        if self.is_current {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Billing period is already current".to_string(),
            });
        }

        if self.payment_status.is_paid() {
            return Err(DomainError::BusinessRuleViolation {
                rule: "Cannot reopen paid billing period".to_string(),
            });
        }

        self.is_current = true;
        self.version += 1;
        Ok(())
    }

    // Getters
    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn user_id(&self) -> Uuid {
        self.user_id
    }

    pub fn period_range(&self) -> &PeriodRange {
        &self.period_range
    }

    pub fn total_requests(&self) -> i32 {
        self.total_requests
    }

    pub fn total_cost(&self) -> Money {
        self.total_cost
    }

    pub fn is_current(&self) -> bool {
        self.is_current
    }

    pub fn payment_status(&self) -> PaymentStatus {
        self.payment_status.clone()
    }

    pub fn paid_at(&self) -> Option<DateTime<Utc>> {
        self.paid_at
    }

    pub fn paid_amount(&self) -> Option<Money> {
        self.paid_amount
    }

    pub fn payment_reference(&self) -> Option<&String> {
        self.payment_reference.as_ref()
    }

    pub fn notes(&self) -> Option<&String> {
        self.notes.as_ref()
    }

    pub fn version(&self) -> i64 {
        self.version
    }

    /// Check if period is due for payment
    pub fn is_due_for_payment(&self) -> bool {
        !self.is_current && !self.payment_status.is_paid()
    }

    /// Check if period is overdue
    pub fn is_overdue(&self) -> bool {
        matches!(self.payment_status, PaymentStatus::Overdue)
    }
}

impl PartialEq for BillingPeriod {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
    }
}

impl Eq for BillingPeriod {}
```

## Verification Steps

1. **Domain Model Compilation**:
   ```bash
   cd backend-rs
   cargo check
   # Should compile without errors
   ```

2. **Unit Tests**:
   ```bash
   cargo test domain
   # Run domain-specific tests
   ```

3. **Business Logic Validation**:
   ```bash
   # Test that domain models enforce business rules
   cargo test user_validation
   cargo test billing_calculations
   ```

## Expected Files Created

### New Files:
- `src/domain/mod.rs`
- `src/domain/shared/mod.rs`
- `src/domain/shared/value_objects.rs`
- `src/domain/shared/events.rs`
- `src/domain/users/mod.rs`
- `src/domain/users/entities.rs`
- `src/domain/users/value_objects.rs`
- `src/domain/users/services.rs`
- `src/domain/users/events.rs`
- `src/domain/billing/mod.rs`
- `src/domain/billing/entities.rs`

### Modified Files:
- `Cargo.toml` (ensure chrono, uuid, serde dependencies)

## Next Task Dependency

This task enables:
- **Task 5**: Repositories (requires domain entities)
- **Task 6**: Authentication (requires user domain)
- **Task 8**: User Management (requires domain models)
- **Task 9**: Core Service (requires domain integration)
- **Task 10**: Billing System (requires billing domain)

## Success Metrics

- [ ] All domain entities compile without errors
- [ ] Business rules are properly enforced
- [ ] Value objects provide proper validation
- [ ] Domain events are well-defined
- [ ] Domain services handle complex business logic
- [ ] No infrastructure dependencies in domain layer
- [ ] Domain models are easily testable
- [ ] Business logic is encapsulated and protected

---

**This task establishes the core business logic foundation with proper domain modeling and business rule enforcement.**