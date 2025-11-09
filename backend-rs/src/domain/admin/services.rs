//! Admin domain services

/// Admin domain service for administrative functions
pub struct AdminDomainService;

impl AdminDomainService {
    /// Validate invite code creation
    pub fn validate_invite_code(code: &str) -> Result<(), crate::domain::DomainError> {
        if code.len() < 6 {
            return Err(crate::domain::DomainError::ValidationError {
                field: "invite_code".to_string(),
                message: "Invite code must be at least 6 characters".to_string(),
            });
        }

        Ok(())
    }
}