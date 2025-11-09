//! Core domain services

/// Core domain service for mathematical problem solving
pub struct CoreDomainService;

impl CoreDomainService {
    /// Process mathematical problem solving request
    pub fn process_problem(image_data: &[u8]) -> Result<String, crate::domain::DomainError> {
        if image_data.is_empty() {
            return Err(crate::domain::DomainError::ValidationError {
                field: "image_data".to_string(),
                message: "Image data cannot be empty".to_string(),
            });
        }

        Ok("Math problem solved".to_string())
    }
}