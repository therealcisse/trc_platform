# Task 1: Project Setup and Foundation

## Description
Initialize the Cargo workspace with all necessary dependencies for the TRC Platform Rust backend. This task creates the fundamental project structure, configures the build system, and sets up the development environment.

## Acceptance Criteria
1. ✅ Create `Cargo.toml` with workspace configuration
2. ✅ Configure all required dependencies with latest versions
3. ✅ Set up project directory structure according to plan
4. ✅ Create basic `main.rs` and `lib.rs` files
5. ✅ Configure development dependencies for testing and quality
6. ✅ Create README.md with project overview and setup instructions
7. ✅ Verify project compiles successfully with `cargo check`

## Prerequisites
- None (this is the foundational task)

## Technical Implementation

### Step 1: Create Cargo.toml
Create `backend-rs/Cargo.toml` with workspace configuration:

```toml
[package]
name = "trc-platform"
version = "0.1.0"
edition = "2021"
authors = ["TRC Platform Team"]
description = "TRC Platform Backend - High-performance Rust implementation"

[workspace]
members = [".", "."]  # Single package workspace for future expansion

[dependencies]
# Web Framework
axum = { version = "0.7", features = ["macros", "tracing"] }
tower = { version = "0.5", features = ["full"] }
tower-http = { version = "0.6", features = ["cors", "trace", "compression"] }
hyper = { version = "1.0", features = ["full"] }

# Database
sqlx = { version = "0.8", features = [
    "postgres",
    "runtime-tokio-rustls",
    "uuid",
    "chrono",
    "json",
    "migrate"
] }

# Authentication & Security
jsonwebtoken = "10.1"
tower-oauth2-resource-server = "0.4"
argon2 = "0.5"
ring = "0.17"

# HTTP Client
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }

# Caching
moka = { version = "0.12", features = ["future"] }
redis = { version = "0.26", features = ["tokio-comp", "connection-manager"] }

# API Documentation
utoipa = { version = "5.4", features = ["axum_extras", "openapi_extensions"] }
utoipa-swagger-ui = { version = "6.0", features = ["axum"] }

# Configuration
figment = { version = "0.10", features = ["env", "toml", "json"] }

# Error Handling
thiserror = "2.0"
anyhow = "1.0"

# Async Runtime
tokio = { version = "1.48", features = ["full"] }

# Logging & Monitoring
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
tracing-opentelemetry = "0.32"
opentelemetry = "0.26"
opentelemetry-otlp = "0.31"

# Utilities
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
uuid = { version = "1.11", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
base64 = "0.22"
once_cell = "1.20"
futures = "0.3"

# Email
lettre = "0.11"

[dev-dependencies]
tokio-test = "0.4"
tempfile = "3.0"

[profile.release]
lto = true
codegen-units = 1
panic = "abort"

[profile.dev]
debug = true
```

### Step 2: Create Directory Structure
Create the following directory structure:

```bash
mkdir -p src/{domain/{users,billing,core,admin},application/{auth,billing,core,admin},infrastructure/{database,cache,email,openai},adapters/{handlers,middleware},config}
mkdir -p migrations
mkdir -p tests
mkdir -p docs/api
```

### Step 3: Create Basic Source Files

#### src/main.rs
```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "trc_platform=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("TRC Platform Rust Backend starting...");

    // TODO: Initialize application
    println!("TRC Platform Rust Backend - Development Mode");
}
```

#### src/lib.rs
```rust
//! TRC Platform Rust Backend
//!
//! A high-performance backend for mathematical problem-solving services
//! built with Rust, Axum, and modern async patterns.

pub mod config;
pub mod domain;
pub mod application;
pub mod infrastructure;
pub mod adapters;

use thiserror::Error;

/// Common application errors
#[derive(Debug, Error)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Authentication error: {0}")]
    Authentication(String),

    #[error("Validation error: {0}")]
    Validation(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Internal server error: {0}")]
    Internal(String),
}

impl axum::response::IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, error_message) = match self {
            AppError::Database(ref e) => {
                tracing::error!("Database error: {:?}", e);
                (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            }
            AppError::Config(ref msg) => {
                tracing::error!("Configuration error: {}", msg);
                (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Configuration error")
            }
            AppError::Authentication(ref msg) => {
                (axum::http::StatusCode::UNAUTHORIZED, msg)
            }
            AppError::Validation(ref msg) => {
                (axum::http::StatusCode::BAD_REQUEST, msg)
            }
            AppError::NotFound(ref msg) => {
                (axum::http::StatusCode::NOT_FOUND, msg)
            }
            AppError::Internal(ref msg) => {
                tracing::error!("Internal error: {}", msg);
                (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            }
        };

        let body = axum::Json(serde_json::json!({
            "error": error_message
        }));

        (status, body).into_response()
    }
}
```

### Step 4: Create Placeholder Modules

#### src/config/mod.rs
```rust
//! Configuration management module
pub mod settings;

pub use settings::*;
```

#### src/config/settings.rs
```rust
//! Application settings and configuration

use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub server: ServerSettings,
    pub database: DatabaseSettings,
    pub openai: OpenAISettings,
    pub jwt: JwtSettings,
    pub email: EmailSettings,
    pub cache: CacheSettings,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerSettings {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseSettings {
    pub url: String,
    pub max_connections: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OpenAISettings {
    pub api_key: String,
    pub model: String,
    pub timeout_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JwtSettings {
    pub secret: String,
    pub ttl_hours: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmailSettings {
    pub smtp_host: String,
    pub smtp_port: u16,
    pub smtp_username: String,
    pub smtp_password: String,
    pub from_address: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CacheSettings {
    pub redis_url: Option<String>,
    pub ttl_seconds: u64,
}
```

#### Create other placeholder module files:
```rust
// src/domain/mod.rs
//! Domain layer - Business entities and logic

pub mod users;
pub mod billing;
pub mod core;
pub mod admin;

// src/application/mod.rs
//! Application layer - Use cases and application services

pub mod auth;
pub mod billing;
pub mod core;
pub mod admin;

// src/infrastructure/mod.rs
//! Infrastructure layer - External services and data access

pub mod database;
pub mod cache;
pub mod email;
pub mod openai;

// src/adapters/mod.rs
//! Adapters layer - HTTP handlers and external integrations

pub mod handlers;
pub mod middleware;

// Create empty placeholder files for each sub-module
```

### Step 5: Create README.md

```markdown
# TRC Platform Rust Backend

A high-performance Rust backend for mathematical problem-solving services, built with modern async patterns and clean architecture.

## Features

- **High Performance**: Built with Rust and Axum for maximum performance
- **Type Safety**: Compile-time query validation with SQLx
- **Security**: JWT and API token authentication with Argon2 password hashing
- **Scalability**: Async/await throughout with connection pooling and caching
- **Documentation**: Auto-generated OpenAPI documentation
- **Monitoring**: Structured logging with tracing and OpenTelemetry

## Quick Start

### Prerequisites
- Rust 1.70+
- PostgreSQL 16+
- Redis (optional, for distributed caching)

### Development Setup

1. **Clone and setup**:
   ```bash
   cd backend-rs
   ```

2. **Install dependencies**:
   ```bash
   cargo build
   ```

3. **Set up environment**:
   ```bash
   export DATABASE_URL="postgresql://trc_user:trc_password@localhost:5432/trc_platform"
   export OPENAI_API_KEY="your-openai-api-key"
   export JWT_SECRET="your-256-bit-secret"
   ```

4. **Run the application**:
   ```bash
   cargo run
   ```

## Development

### Running Tests
```bash
cargo test
```

### Code Quality
```bash
cargo check
cargo clippy
cargo fmt --check
```

### Database Migrations
```bash
# Run migrations
sqlx migrate run

# Create new migration
sqlx migrate add <migration_name>
```

## Architecture

This project follows **Clean Architecture** principles:

- **Domain**: Core business logic and entities
- **Application**: Use cases and application services
- **Infrastructure**: External services and data access
- **Adapters**: HTTP handlers and external integrations

## Configuration

The application uses Figment for configuration management. Configuration can be provided through:
- Environment variables
- `config.toml` file
- `config.json` file

See `src/config/settings.rs` for available configuration options.

## API Documentation

Once running, API documentation is available at:
- Swagger UI: `http://localhost:8080/swagger-ui/`
- OpenAPI JSON: `http://localhost:8080/api-docs/openapi.json`

## License

This project is part of the TRC Platform.
```

## Verification Steps

1. **Project Structure Verification**:
   ```bash
   tree -I 'target' backend-rs/
   # Should show all directories created
   ```

2. **Compilation Check**:
   ```bash
   cd backend-rs
   cargo check
   # Should complete without errors
   ```

3. **Dependency Resolution**:
   ```bash
   cargo tree
   # Should show all dependencies resolved
   ```

4. **Basic Run Test**:
   ```bash
   cargo run
   # Should start and show "TRC Platform Rust Backend - Development Mode"
   ```

## Expected Files Created

After completing this task, the following files should exist:

```
backend-rs/
├── Cargo.toml
├── README.md
├── src/
│   ├── main.rs
│   ├── lib.rs
│   ├── config/
│   │   ├── mod.rs
│   │   └── settings.rs
│   ├── domain/
│   │   └── mod.rs
│   ├── application/
│   │   └── mod.rs
│   ├── infrastructure/
│   │   └── mod.rs
│   └── adapters/
│       └── mod.rs
├── migrations/
├── tests/
└── docs/
    └── api/
```

## Next Task Dependency

This task must be completed before:
- **Task 2**: Database Schema (requires project structure)
- **Task 3**: Configuration (requires basic config module)
- All subsequent tasks

## Troubleshooting

- **Compilation Issues**: Ensure Rust 1.70+ is installed
- **Dependency Conflicts**: Run `cargo update` to resolve versions
- **Missing Directories**: Verify all directories were created with `mkdir -p`

## Success Metrics

- [ ] `cargo check` completes without errors
- [ ] `cargo run` starts the application
- [ ] All directories are created correctly
- [ ] README.md provides clear setup instructions
- [ ] Project structure matches the architectural plan

---

**This task provides the foundation for all subsequent implementation tasks.**