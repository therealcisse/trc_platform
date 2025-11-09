//! Billing domain services

/// Billing domain service for complex business logic
pub struct BillingDomainService;

impl BillingDomainService {
    /// Calculate total cost for a billing period
    pub fn calculate_total_cost(requests: i32, cost_per_request: i64) -> i64 {
        requests as i64 * cost_per_request
    }
}