//! User domain services

/// User domain service for complex business logic
pub struct UserDomainService;

impl UserDomainService {
    /// Validate user registration data
    pub fn validate_registration(email: &str, password: &str) -> Result<(), crate::domain::DomainError> {
        if password.len() < 8 {
            return Err(crate::domain::DomainError::ValidationError {
                field: "password".to_string(),
                message: "Password must be at least 8 characters".to_string(),
            });
        }

        Ok(())
    }
}