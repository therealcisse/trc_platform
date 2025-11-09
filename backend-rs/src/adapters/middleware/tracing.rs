//! Tracing middleware

use axum::{
    extract::Request,
    middleware::Next,
    response::Response,
};
use uuid::Uuid;

pub async fn tracing_middleware(
    request: Request,
    next: Next,
) -> Response {
    let request_id = Uuid::new_v4().to_string();

    tracing::info!(
        request_id = %request_id,
        method = %request.method(),
        uri = %request.uri(),
        "Incoming request"
    );

    let response = next.run(request).await;

    tracing::info!(
        request_id = %request_id,
        status = %response.status(),
        "Request completed"
    );

    response
}