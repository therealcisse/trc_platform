use axum::{
    Router,
    routing::get,
    http::StatusCode,
    response::Json,
};
use std::net::SocketAddr;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use tracing::info;

use trc_platform::{HandlerState, config::ConfigService};
use trc_platform::adapters::handlers::{health, info};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "trc_platform=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    info!("TRC Platform Rust Backend starting...");

    // Initialize configuration
    let config_service = std::sync::Arc::new(
        ConfigService::new()
            .map_err(|e| format!("Failed to load configuration: {}", e))?
    );

    // Initialize application state
    let handler_state = HandlerState::new(config_service.clone()).await?;

    // Build our application with routes
    let app = Router::new()
        .route("/health", get(health::health_check))
        .route("/info", get(info::app_info))
        .with_state(handler_state)
        .layer(
            tower::ServiceBuilder::new()
                .layer(axum::middleware::from_fn(
                    trc_platform::adapters::middleware::tracing::tracing_middleware
                ))
                .layer(
                    trc_platform::adapters::middleware::cors::cors_layer()
                )
                .into_inner(),
        );

    // Get server address from config
    let addr: SocketAddr = config_service.settings().bind_address();

    info!("Server listening on {}", addr);

    // Run the server
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await?;

    Ok(())
}