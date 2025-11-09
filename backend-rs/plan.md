# TRC Platform Rust Backend Implementation Plan

## Overview
Create a modern, high-performance Rust backend in `backend-rs/` that replicates and enhances the Java Spring Boot application's functionality using 2024-2025 best practices.

## Technology Stack (Latest Versions)

### Core Framework
- **Web Framework**: Axum 0.7+ (built by Tokio team, excellent async support)
- **Database**: SQLx 0.8+ (compile-time checked queries, async-first)
- **Authentication**: JSONwebtoken 10.1 + tower-oauth2-resource-server 0.4
- **HTTP Client**: Reqwest 0.12+ (async, TLS support)
- **Caching**: Moka 0.12+ (in-memory) + Redis 0.26+ (distributed)

### Architecture & Quality
- **Pattern**: Hexagonal/Clean Architecture for maintainability
- **Config**: Figment 0.10+ (type-safe, hierarchical)
- **Error Handling**: thiserror 2.0 + anyhow 1.0
- **Documentation**: Utoipa 5.4+ (compile-time OpenAPI generation)
- **Logging**: tracing 0.1 + tracing-subscriber 0.3 (structured logging)

## Project Structure
```
backend-rs/
├── Cargo.toml
├── Dockerfile
├── docker-compose.yml
├── README.md
├── plan.md
├── docs/
│   └── api/           # Generated OpenAPI documentation
├── src/
│   ├── main.rs
│   ├── lib.rs
│   ├── domain/        # Business logic, entities
│   │   ├── users/
│   │   ├── billing/
│   │   ├── core/
│   │   └── admin/
│   ├── application/   # Use cases, services
│   │   ├── auth/
│   │   ├── billing/
│   │   ├── core/
│   │   └── admin/
│   ├── infrastructure/ # Database, external APIs
│   │   ├── database/
│   │   ├── cache/
│   │   ├── email/
│   │   └── openai/
│   ├── adapters/      # HTTP handlers
│   │   ├── handlers/
│   │   └── middleware/
│   └── config/        # Configuration management
├── migrations/        # SQLx database migrations
│   ├── V1__Create_initial_schema.sql
│   └── V2__Add_performance_indexes.sql
└── tests/            # Integration tests
```

## Implementation Tasks

This project is broken down into 15 detailed, AI-implementable tasks located in the `tasks/` directory:

### Phase 1: Foundation (Tasks 1-3)
1. **[Project Setup](tasks/01-project-setup.md)** - Initialize Cargo workspace and dependencies
2. **[Database Schema](tasks/02-database-schema.md)** - Create SQLx migrations matching Java schema
3. **[Configuration](tasks/03-configuration.md)** - Setup Figment-based configuration management

### Phase 2: Core Infrastructure (Tasks 4-6)
4. **[Domain Models](tasks/04-domain-models.md)** - Implement core business entities
5. **[Repositories](tasks/05-repositories.md)** - Create database access layer with SQLx
6. **[Authentication](tasks/06-authentication.md)** - Implement JWT and API token security

### Phase 3: Web Framework (Tasks 7-8)
7. **[Web Framework](tasks/07-web-framework.md)** - Setup Axum with middleware and routing
8. **[User Management](tasks/08-user-management.md)** - Implement registration, login, and API tokens

### Phase 4: Business Logic (Tasks 9-11)
9. **[Core Service](tasks/09-core-service.md)** - OpenAI integration for math problem solving
10. **[Billing System](tasks/10-billing-system.md)** - Usage tracking and period-based billing
11. **[Admin Endpoints](tasks/11-admin-endpoints.md)** - Administrative functions and invite codes

### Phase 5: Documentation & Performance (Tasks 12-15)
12. **[API Documentation](tasks/12-api-documentation.md)** - OpenAPI generation and Swagger UI
13. **[Caching](tasks/13-caching.md)** - Multi-level caching with Moka and Redis
14. **[Monitoring](tasks/14-monitoring.md)** - Logging, tracing, and observability
15. **[Docker Deployment](tasks/15-docker-deployment.md)** - Production containerization

## Key Implementation Decisions

### Database Design
- **UUID Primary Keys**: Use uuid 1.11 with v4 generation
- **Optimistic Locking**: Version columns for concurrency control
- **Migration Strategy**: SQLx for consistent schema management
- **Connection Pooling**: SQLx built-in pooling with optimized settings

### Security Architecture
- **Multi-factor Auth**: Email verification + invite codes
- **Token Management**: JWT for sessions, API tokens for programmatic access
- **Password Security**: Argon2 hashing with proper parameters
- **Input Validation**: Type-safe validation using serde and custom validators

### Performance Optimizations
- **Async-First**: Full async/await throughout the stack
- **Connection Pooling**: Optimized database and Redis connections
- **Caching Strategy**: L1 (Moka) + L2 (Redis) with TTL management
- **Memory Efficiency**: Zero-copy parsing where possible

### Error Handling Strategy
- **Domain Errors**: thiserror for business logic errors
- **HTTP Mapping**: Proper error-to-status-code conversion
- **Structured Logging**: tracing with correlation IDs
- **Graceful Degradation**: Fallback mechanisms for external services

## Dependency Stack

```toml
[dependencies]
# Web Framework
axum = { version = "0.7", features = ["macros", "tracing"] }
tower = { version = "0.5", features = ["full"] }
tower-http = { version = "0.6", features = ["cors", "trace", "compression"] }

# Database
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio-rustls", "uuid", "chrono", "json"] }

# Authentication & Security
jsonwebtoken = "10.1"
tower-oauth2-resource-server = "0.4"
argon2 = "0.5"

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

# Utilities
serde = { version = "1.0", features = ["derive"] }
uuid = { version = "1.11", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
```

## Success Criteria
1. **Functional Parity**: All Java backend features replicated
2. **Performance**: Target 2-3x performance improvement over Java
3. **Maintainability**: Clean architecture with clear separation of concerns
4. **Documentation**: Auto-generated API docs with 100% coverage
5. **Production Ready**: Containerized deployment with monitoring
6. **AI-Implementable**: Each task detailed enough for independent AI implementation

## Implementation Guidelines

### For AI Implementation
Each task in the `tasks/` directory is designed to be:
- **Self-contained**: Clear scope and deliverables
- **Detailed**: Specific code examples and file structures
- **Testable**: Clear acceptance criteria and verification steps
- **Sequential**: Proper dependency management between tasks
- **Complete**: All necessary information for independent implementation

### Quality Standards
- Follow Rust best practices and idiomatic code
- Implement proper error handling for all operations
- Use type-safe patterns throughout
- Include comprehensive logging and monitoring
- Maintain clean architecture principles
- Ensure thread safety and performance optimization

This plan provides a comprehensive roadmap for building a high-quality, production-ready Rust backend that maintains and enhances the functionality of the existing Java Spring Boot application.