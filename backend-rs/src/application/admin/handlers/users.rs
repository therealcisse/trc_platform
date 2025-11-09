//! Admin user management handlers

use axum::{
    extract::{State, Path, Query},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize)]
pub struct ListUsersQuery {
    pub page: Option<u32>,
    pub limit: Option<u32>,
    pub search: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UserResponse {
    pub id: String,
    pub email: String,
    pub full_name: String,
    pub status: String,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UsersListResponse {
    pub users: Vec<UserResponse>,
    pub total: u64,
    pub page: u32,
    pub limit: u32,
}

pub async fn list_users(
    State(_state): State<crate::HandlerState>,
    Query(query): Query<ListUsersQuery>,
) -> impl IntoResponse {
    // TODO: Implement user listing with pagination and search
    tracing::info!("Admin listing users with query: {:?}", query);

    let response = UsersListResponse {
        users: vec![],
        total: 0,
        page: query.page.unwrap_or(1),
        limit: query.limit.unwrap_or(20),
    };

    (StatusCode::OK, Json(response)).into_response()
}

pub async fn get_user(
    State(_state): State<crate::HandlerState>,
    Path(user_id): Path<String>,
) -> impl IntoResponse {
    // TODO: Implement user details retrieval
    tracing::info!("Admin getting user: {}", user_id);

    let response = UserResponse {
        id: user_id,
        email: "user@example.com".to_string(),
        full_name: "John Doe".to_string(),
        status: "active".to_string(),
        created_at: "2024-01-01T00:00:00Z".to_string(),
    };

    (StatusCode::OK, Json(response)).into_response()
}