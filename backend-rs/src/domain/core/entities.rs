//! Core domain entities

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::net::IpAddr;

/// Mathematical problem solving request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MathProblem {
    pub id: Uuid,
    pub image_data: Vec<u8>,
    pub user_id: Uuid,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

/// Mathematical problem solution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MathSolution {
    pub problem_id: Uuid,
    pub result: String,
    pub steps: Vec<String>,
    pub confidence: f64,
}

/// HTTP request log entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RequestLog {
    id: Uuid,
    user_id: Option<Uuid>,
    api_token_id: Option<Uuid>,
    method: String,
    path: String,
    status_code: u16,
    response_time_ms: Option<u32>,
    request_size_bytes: Option<u64>,
    response_size_bytes: Option<u64>,
    ip_address: Option<IpAddr>,
    user_agent: Option<String>,
    status: RequestStatus,
    error_message: Option<String>,
    created_at: DateTime<Utc>,
}

/// Request status enum
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum RequestStatus {
    Success,
    Error,
    Timeout,
}

impl RequestLog {
    pub fn new(
        user_id: Option<Uuid>,
        api_token_id: Option<Uuid>,
        method: String,
        path: String,
        status_code: u16,
    ) -> Self {
        Self {
            id: Uuid::new_v4(),
            user_id,
            api_token_id,
            method,
            path,
            status_code,
            response_time_ms: None,
            request_size_bytes: None,
            response_size_bytes: None,
            ip_address: None,
            user_agent: None,
            status: if status_code < 400 {
                RequestStatus::Success
            } else {
                RequestStatus::Error
            },
            error_message: None,
            created_at: Utc::now(),
        }
    }

    pub fn id(&self) -> Uuid {
        self.id
    }

    pub fn user_id(&self) -> Option<Uuid> {
        self.user_id
    }

    pub fn is_success(&self) -> bool {
        matches!(self.status, RequestStatus::Success)
    }

    pub fn set_response_time(&mut self, response_time_ms: u32) {
        self.response_time_ms = Some(response_time_ms);
    }

    pub fn set_ip_address(&mut self, ip_address: IpAddr) {
        self.ip_address = Some(ip_address);
    }

    pub fn set_user_agent(&mut self, user_agent: String) {
        self.user_agent = Some(user_agent);
    }

    pub fn set_error_message(&mut self, error_message: String) {
        self.error_message = Some(error_message);
        self.status = RequestStatus::Error;
    }
}