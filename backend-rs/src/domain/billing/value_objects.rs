//! Billing domain value objects

use serde::{Deserialize, Serialize};
use crate::domain::DomainError;

/// Money value object for financial calculations
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Money {
    amount_cents: i64,
}

impl Money {
    pub fn new_cents(cents: i64) -> Result<Self, DomainError> {
        if cents < 0 {
            return Err(DomainError::ValidationError {
                field: "amount".to_string(),
                message: "Amount cannot be negative".to_string(),
            });
        }

        Ok(Money { amount_cents: cents })
    }

    pub fn cents(&self) -> i64 {
        self.amount_cents
    }
}