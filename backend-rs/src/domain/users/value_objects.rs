//! User domain value objects

use serde::{Deserialize, Serialize};
use crate::domain::DomainError;

/// Email value object with validation
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Email(String);

impl Email {
    pub fn new(email: &str) -> Result<Self, DomainError> {
        let email = email.trim().to_lowercase();

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

        Ok(Email(email))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl Default for Email {
    fn default() -> Self {
        Email("user@example.com".to_string())
    }
}