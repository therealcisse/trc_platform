//! Domain layer - Business entities and logic

pub mod users;
pub mod billing;
pub mod core;
pub mod admin;

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

pub type DomainResult<T> = Result<T, DomainError>;