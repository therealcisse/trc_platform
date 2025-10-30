# TRC Platform Java Backend Implementation Prompt

## Overview

You are a Senior Java Software Architect tasked with implementing a complete Java Spring Boot backend for the TRC Platform. **You must strictly follow the technical specifications provided in `@JAVA_TECHNICAL_SPECIFICATION.md`** as your primary reference document. This implementation will replace an existing Django backend while maintaining 100% functional compatibility.

## Project Context & Business Vision

### Business Vision & Mission
The TRC Platform is an AI-powered mathematical problem-solving service that transforms mathematical problem-solving from a manual, time-consuming process into an automated, instant experience. Our mission is to **democratize access to mathematical problem-solving capabilities** by providing an easy-to-use, affordable, and reliable platform that leverages artificial intelligence to help students, educators, and professionals solve mathematical problems efficiently.

### Core Value Proposition
Users simply upload an image containing a mathematical problem, and our AI-powered system analyzes and provides accurate solutions within seconds. This eliminates the frustration and time traditionally spent on manual problem-solving, enabling users to focus on understanding concepts rather than computational mechanics.

### Target User Personas
Understanding our users is critical for technical decisions:

**Primary Users:**
- **Student Sarah** (16-24, high school/college): Needs instant homework help, values speed and accuracy, uses mobile and desktop platforms during study periods
- **Educator Emma** (25-55, teacher/tutor): Requires reliable verification tools, batch processing capabilities, and integration with educational platforms
- **Developer David** (25-45, software engineer): Needs reliable APIs for application integration, automated workflows, and scalable pricing

**Secondary Users:**
- **Admin Alex** (28-50, operations): Manages system health, user accounts, billing oversight, and requires comprehensive monitoring tools

### Business Objectives & Success Metrics
The technical implementation must directly support these business goals:
- **User Growth**: Achieve 10,000+ Monthly Active Users (MAU) within first year
- **Performance Excellence**: Maintain 99.9% uptime with sub-2-second response times
- **Accuracy Standards**: Achieve 95%+ accuracy rate for mathematical problem solutions
- **Revenue Sustainability**: Implement usage-based billing that scales with user growth
- **Market Leadership**: Become the leading AI-powered mathematical problem-solving platform

### Core Platform Features
The platform delivers value through these key capabilities:
- **Controlled User Onboarding**: Invite-code based registration for quality control and gradual scaling
- **AI-Powered Problem Solving**: Advanced image analysis using OpenAI Vision API with mathematical specialization
- **Dual Authentication System**: Session-based (web) and token-based (API) authentication for different use cases
- **Comprehensive Usage Tracking**: Detailed request logging with billing period management
- **Administrative Excellence**: Complete admin interface for user management and system oversight
- **Domain Separation Architecture**: Proper frontend-backend separation for security and scalability

## Implementation Requirements

### 1. Project Structure

**Create the new Java project in the `backend-java/` folder** with the following Maven structure:

```
backend-java/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── trc/
│   │   │           └── platform/
│   │   │               ├── TrcPlatformApplication.java
│   │   │               ├── config/
│   │   │               ├── common/
│   │   │               ├── security/
│   │   │               ├── users/
│   │   │               ├── core/
│   │   │               ├── usage/
│   │   │               └── monitoring/
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       └── db/migration/
│   └── test/
│       └── java/
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### 2. Technology Stack Implementation

Implement using the specified technology stack:

**Core Technologies:**
- **Java 21 LTS** - Use modern features (records, virtual threads, switch expressions)
- **Spring Boot 3.3.x** - Current stable version with Jakarta EE
- **Spring Security 6.3.x** - Comprehensive security framework
- **Spring Data JPA/Hibernate 3.2.x** - ORM with caching
- **PostgreSQL 16+** - Primary database
- **Maven 3.9.x** - Build and dependency management

**Additional Technologies:**
- **Jakarta Bean Validation 3.0.x** - Input validation
- **Spring Cache + Caffeine** - In-memory caching (Redis-ready for future)
- **Spring WebFlux WebClient** - Non-blocking HTTP client for OpenAI
- **Spring Mail** - Email service integration
- **Flyway** - Database migrations
- **JUnit 5 + Testcontainers** - Testing framework
- **SpringDoc OpenAPI 3.0** - API documentation

### 3. Architecture Implementation

**Module Structure (as specified):**
- **users/**: User management, authentication, API tokens
- **core/**: Image processing, OpenAI integration, file handling
- **usage/**: Billing periods, request logs, analytics
- **security/**: Multi-modal authentication (session + API tokens)
- **common/**: Shared utilities, exceptions, DTOs
- **config/**: Configuration classes, caching, security setup

**Layer Architecture:**
Each module must follow strict layered architecture:
- **Controller Layer**: REST endpoints with validation
- **Service Layer**: Business logic and domain rules
- **Repository Layer**: Data access with JPA
- **DTO Layer**: Request/response objects with proper validation

### 4. Database Implementation

**Entity Design:**
Implement all entities as **explicitly detailed in `@JAVA_TECHNICAL_SPECIFICATION.md` section 4.2**:
- `User` with proper relationships and audit fields
- `ApiToken` with hash-based security and usage tracking
- `BillingPeriod` with payment status and period management
- `RequestLog` with comprehensive logging and indexing
- `Settings` as singleton pattern with caching

**Database Configuration:**
- Use HikariCP connection pooling with optimized settings
- Implement Flyway migrations for schema management
- Add proper indexes for performance optimization
- Use PostgreSQL-specific features where appropriate

**Migration Strategy:**
- Create initial Flyway migration `V1__Create_initial_schema.sql`
- Ensure all entities match Django model structure exactly
- Include constraints, indexes, and proper data types

### 5. Security Implementation

**Multi-Modal Authentication:**
- **Session Authentication**: JWT-based for web interface
- **API Token Authentication**: Hashed tokens for programmatic access
- Proper security filters chain with both authentication methods

**Authorization:**
- Role-based access control (USER, ADMIN)
- Method-level security with `@PreAuthorize`
- Proper permission-based access control

**Security Best Practices:**
- Password hashing with BCrypt
- CORS configuration for specific origins
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Input validation and sanitization
- Rate limiting considerations

### 6. API Implementation with User Experience Focus

**API Design Philosophy:**
Every API endpoint must support our user personas' needs and business objectives:

**For Student Sarah (Speed & Convenience):**
- Sub-2 second response times for instant homework help
- Mobile-friendly endpoints with proper error handling
- Clear, concise responses that work well on small screens

**For Educator Emma (Reliability & Integration):**
- Consistent, reliable responses with 95%+ accuracy
- Batch processing capabilities through API tokens
- Comprehensive usage tracking for classroom management

**For Developer David (Scalability & Integration):**
- Well-documented APIs with OpenAPI 3.0 specifications
- Robust error handling and retry mechanisms
- Scalable architecture supporting high-volume requests

**For Admin Alex (Monitoring & Management):**
- Comprehensive admin endpoints for system oversight
- Real-time monitoring and analytics capabilities
- User management tools for account administration

**REST API Design:**
Implement all endpoints as **explicitly specified in `@JAVA_TECHNICAL_SPECIFICATION.md` section 5**:

**Authentication Endpoints:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/password/change` - Change password
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/resend-verification` - Resend verification email
- `POST /api/auth/accept-terms` - Accept terms
- `POST /api/auth/accept-disclaimer` - Accept disclaimer

**User Management:**
- `GET /api/customers/me` - Current user profile
- `GET/POST /api/customers/tokens` - API token management
- `DELETE /api/customers/tokens/{token_id}` - Revoke API token

**Core Processing:**
- `POST /api/core/solve` - Math problem solving (multipart)
- `POST /api/core/test-solve` - Test solve endpoint (development/testing)
- `GET /api/core/health` - Health check endpoint

**Usage and Billing:**
- `GET /api/usage/summary` - Usage statistics
- `GET /api/usage/requests` - Request history

**Billing Period Management:**
- `GET /api/billing/current` - Current billing period
- `GET /api/billing/periods` - List all billing periods (paginated)
- `GET /api/billing/periods/{period_id}` - Billing period details with requests

**Settings Management:**
- `GET/PUT /api/v1/admin/settings` - Application settings

**API Standards:**
- Consistent response format using `ApiResponse<T>` wrapper
- Proper HTTP status codes
- Comprehensive error handling with specific error codes
- OpenAPI 3.0 documentation generation

### 7. Core Business Logic

**OpenAI Integration:**
- Implement `OpenAIClientService` with WebClient
- Proper error handling and retry logic
- Circuit breaker pattern for resilience
- Base64 image encoding for vision API
- Dynamic configuration through settings service

**Image Processing:**
- Support for common image formats (JPEG, PNG)
- File size validation and limits
- Temporary file handling with cleanup
- Error handling for invalid images

**Usage Tracking:**
- Automatic request logging
- Billing period management
- Cost calculation based on settings
- Usage statistics and reporting

### 8. Caching Implementation

**Dual Caching Strategy:**
- **Primary**: Caffeine in-memory cache for development
- **Redis-Ready**: Configuration prepared for Redis in production

**Cache Configuration:**
- User cache: 1-hour TTL
- API token cache: 30-minute TTL
- Settings cache: 5-minute TTL (for quick updates)
- Flow response cache: 2-hour TTL

**Settings Service:**
- Database-backed settings with automatic caching
- Cache invalidation on updates
- Event-driven cache management

### 9. Development Environment

**Docker Compose Setup:**
Create comprehensive `docker-compose.yml` for development:
- Java application container
- PostgreSQL 16 database
- Redis cache (optional for development)
- Proper volumes and networking
- Environment variable configuration

**Development Profile:**
- Debug support with JDWP
- Detailed logging
- Hot reload capabilities
- Database initialization scripts

### 10. Testing Strategy

**Test Structure:**
- Unit tests for all service classes
- Integration tests for repositories
- Controller tests with `@WebMvcTest`
- End-to-end tests with `@SpringBootTest`
- Testcontainers for database testing

**Test Coverage:**
- Minimum 80% code coverage
- Critical paths 100% covered
- Mock external services (OpenAI)
- Test data builders for object creation

### 11. Configuration Management

**Profile-Based Configuration:**
- `application.yml` - Base configuration
- `application-dev.yml` - Development settings
- `application-prod.yml` - Production settings

**Environment Variables:**
- Database connection settings
- OpenAI API key
- Email service configuration
- Application-specific settings

### 12. Error Handling and Logging

**Global Exception Handling:**
- `@RestControllerAdvice` for centralized error handling
- Custom exception hierarchy
- Consistent error response format
- Proper HTTP status codes

**Logging Strategy:**
- Structured logging with Logback
- Different configurations for dev/prod
- JSON logging for production
- Security audit logging

### 13. Performance Considerations

**Database Optimization:**
- Proper connection pooling
- Query optimization with projections
- Batch processing for bulk operations
- Lazy loading where appropriate

**HTTP Client Optimization:**
- Connection pooling in WebClient
- Timeout configurations
- Retry and circuit breaker patterns
- Compression support

### 14. Code Quality and Standards

**IMPORTANT - Reference Implementation Details:**
Throughout this implementation, you **must reference the detailed code examples, configurations, and implementation patterns provided in `@JAVA_TECHNICAL_SPECIFICATION.md`**. The specification includes:

- Complete entity class definitions with all JPA annotations (Section 4.2)
- Frontend-backend architecture with email verification URL construction (Section 4.4)
- Complete controller implementations with all endpoints (Section 6.1-6.4)
- Full security configuration code examples (Section 7.1-7.4)
- Complete API endpoint specifications (Section 5.3-5.7)
- OpenAI client service implementation (Section 8.1.5)
- Settings service with caching (Section 8.1.2)
- Database configuration with connection pooling (Section 4.5)
- Exception handling patterns (Section 10.1.2)

**Use these code examples as your primary implementation guide** - they provide the exact structure, annotations, and patterns to follow.

**Complete Implementation Requirements:**

### 1. Additional DTOs and Entities
You must implement all DTOs specified in **Section 4.2.7** of the technical specification:
- `PasswordChangeRequest` - For password changes
- `EmailVerificationRequest` - For email verification
- `ResendVerificationRequest` - For resending verification emails
- `AcceptTermsRequest` - For terms/disclaimer acceptance
- `BillingPeriodDetailDto` - For detailed billing period views

### 2. Extended Repository Interfaces
Implement all repository extensions specified in **Section 4.3.6**:
- `UserRepository` with methods for email lookup, password updates, email verification
- `BillingPeriodRepository` with methods for period management and request lookup

### 3. Extended Service Methods
Implement all authentication and billing service methods specified in **Section 4.3.7**:
- `AuthenticationService.logout()` - Session invalidation
- `AuthenticationService.changePassword()` - Password update with validation
- `AuthenticationService.verifyEmail()` - Email verification processing
- `AuthenticationService.resendVerificationEmail()` - Verification email resend
- `AuthenticationService.acceptTerms()` - Terms acceptance tracking
- `AuthenticationService.acceptDisclaimer()` - Disclaimer acceptance tracking
- `BillingService.getBillingPeriodDetail()` - Detailed period view with requests
- `BillingService.createNewBillingPeriod()` - Period creation and management

### 4. Controller Methods
All controllers must include methods for:
- User logout with proper session invalidation
- Password change with current password validation
- Email verification and resend functionality
- Terms and disclaimer acceptance endpoints
- API token revocation with DELETE endpoint
- Test solve endpoint (similar to main solve but marked as test)
- Billing period detail endpoint with associated requests

### 5. Critical Implementation Details
**IMPORTANT:** Ensure exact API compatibility by using the correct response structures:

**SolveResponse DTO Structure:**
```java
{
    "requestId": "uuid",
    "result": "math problem solution",
    "durationMs": 1500,
    "timings": {
        "extract_ms": 50,
        "settings_ms": 10,
        "openai_ms": 1400,
        "total_ms": 1500
    }
}
```

**HealthResponse DTO Structure:**
```java
{
    "status": "ok" | "degraded",
    "checks": {
        "database": true | false,
        "openai": true | false
    }
}
```

These structures MUST match the existing Django implementation exactly for 100% API compatibility.

### 6. Frontend-Backend Domain Separation
**CRITICAL ARCHITECTURAL REQUIREMENT:**

You must implement proper frontend-backend domain separation for email verification:

**EmailVerificationService Implementation:**
- Build verification URLs using `Settings.appDomain` when configured
- Fall back to backend domain when `appDomain` is empty (development)
- Generate URLs that point to frontend application, not backend API
- Example: `https://app.trc-platform.com/verify-email?token={token}`

**Settings Management:**
- `appDomain` field already exists in Settings entity (Section 4.2.6)
- Provide admin interface for configuring frontend domain
- Implement CLI command for domain management
- Validate URL format and enforce HTTPS in production

**User Experience Flow:**
1. Backend generates email with frontend verification URL
2. User clicks link → Opens frontend application
3. Frontend extracts token → Calls backend `/api/customers/verify-email`
4. Backend verifies token → Returns success response

This ensures **proper separation of concerns** while maintaining seamless user experience. Refer to **Section 4.4** for detailed implementation requirements.

### 7. CORS Configuration for Frontend-Backend Separation

**CRITICAL REQUIREMENT:**

Since frontend and backend are served from different domains, implement comprehensive CORS configuration:

**Environment-Based CORS Configuration:**
- **Production**: Allow `https://app.trc-platform.com`, `https://admin.trc-platform.com`
- **Development**: Allow `http://localhost:3000`, `http://localhost:5173`
- **Dynamic**: Support `CORS_ALLOWED_ORIGINS` environment variable override

**Implementation Requirements:**
- **Credentials**: Enable `allowCredentials(true)` for session-based authentication
- **Methods**: Support all REST methods including OPTIONS for pre-flight
- **Headers**: Allow `Authorization`, `Content-Type`, `X-CSRFToken`, `X-Requested-With`
- **API Scope**: Apply CORS to `/api/**` endpoints

**Security Integration:**
- CORS works with both session auth and API token authentication
- CSRF token headers allowed for frontend-backend communication
- Pre-flight request handling with proper caching

Refer to **Section 4.5** for detailed CORS strategy and implementation examples.

**Code Style:**
- Google Java Format integration
- Checkstyle configuration
- SpotBugs for static analysis
- Proper JavaDoc documentation

**Design Patterns:**
- Service layer pattern
- Repository pattern
- DTO pattern
- Builder pattern for complex objects
- Strategy pattern for different processing flows

**Best Practices:**
- SOLID principles adherence
- Dependency injection
- Immutability where possible
- Defensive programming
- Null safety with Optional

## Implementation Instructions

### Phase 1: Project Setup and Core Structure
1. Initialize Maven project with required dependencies
2. Set up package structure following technical specification
3. Configure basic Spring Boot application
4. Set up database configuration with HikariCP
5. Create initial Flyway migration

### Phase 2: Domain Model and Database
1. Implement all JPA entities as specified
2. Create repository interfaces
3. Set up relationships and constraints
4. Create database indexes for performance
5. Test database operations

### Phase 3: Security Implementation
1. Set up Spring Security configuration
2. Implement JWT session authentication
3. Implement API token authentication
4. Create user authentication service
5. Set up authorization framework

### Phase 4: Core Business Logic
1. Implement OpenAI client service
2. Create image processing service
3. Implement usage tracking logic
4. Create settings management service
5. Set up email service integration

### Phase 5: API Implementation
1. Implement all REST endpoints as specified
2. Add comprehensive validation
3. Create consistent response format
4. Generate OpenAPI documentation
5. Add global exception handling

### Phase 6: Development Environment
1. Create Dockerfile for application
2. Set up docker-compose.yml for development
3. Configure development profile
4. Add logging and monitoring setup
5. Create comprehensive documentation

### Phase 7: Testing and Quality
1. Implement unit and integration tests
2. Add end-to-end tests
3. Configure code quality tools
4. Set up CI pipeline configuration
5. Performance testing and optimization

## Deliverables

1. **Complete Spring Boot Application** in `backend-java/` folder
2. **Docker Compose Configuration** for local development
3. **Database Migration Scripts** compatible with existing Django data
4. **Comprehensive Test Suite** with >80% coverage
5. **API Documentation** generated by SpringDoc OpenAPI
6. **Documentation** including setup and deployment guides

## Quality Assurance

**Code Quality Checklist:**
- [✓] All entities match Django models exactly
- [✓] All API endpoints implemented with correct responses
- [✓] Security properly implemented with both auth methods
- [✓] Database schema optimized with proper indexes
- [✓] Error handling covers all edge cases
- [✓] Caching properly configured and working
- [✓] Tests provide good coverage of business logic
- [✓] Code follows Java best practices and conventions
- [✓] Documentation is comprehensive and clear
- [✓] Docker setup works for local development

**NEW - Admin System Requirements:**
- [✓] Admin-only invite code management system implemented
- [✓] Billing period administration capabilities added
- [✓] User management interface for administrators
- [✓] Request log analytics and filtering system
- [✓] System health monitoring and cache management
- [✓] Comprehensive admin permissions framework

**NEW - Entity Enhancements:**
- [✓] InviteCode entity properly implemented with Django compatibility
- [✓] @Version fields added for optimistic locking
- [✓] ApiToken entity enhanced with revokedAt field
- [✓] Complete entity relationship mappings implemented

**NEW - Frontend-Backend Separation:**
- [✓] appDomain configuration for email verification URLs
- [✓] Email verification URL construction method
- [✓] CORS configuration for cross-origin requests
- [✓] Proper domain separation architecture implemented

## Important Notes

1. **No Kubernetes Configuration Initially**: Focus on Docker Compose for development only

## Critical Architecture Updates

### **NEW - Admin Management System Requirements:**

**Admin-Only Operations (Critical):**
- **Invite Code Management**: Invite codes are ADMIN-ONLY, not user-facing. Move all invite code endpoints to `/api/v1/admin/invites` with proper permissions
- **Billing Period Administration**: All billing period status changes (paid/overdue/waived) are admin-only operations under `/api/v1/admin/billing/periods/{periodId}/*`
- **User Management**: Comprehensive user administration including viewing user details, managing active status, and API token oversight
- **Request Log Analytics**: Advanced request log viewing with filtering by date, user, status for admin oversight
- **System Monitoring**: Real-time system health checks and cache management for admin dashboard

**Frontend-Backend Domain Separation (Critical):**
- Implement proper `appDomain` configuration in Settings entity
- Email verification URLs MUST point to frontend application, not backend API
- Use SettingsService.buildVerificationUrl() method for consistent URL construction
- CORS configuration must support frontend-backend architecture

### **NEW - Enhanced Entity Requirements:**

**InviteCode Entity Implementation:**
- Complete InviteCode entity as specified in Section 4.2.8 of technical specification
- One-time use codes with proper validation and expiration tracking
- Secure admin-only creation and management
- Proper relationships with User entity for audit trails

**Entity Optimizations:**
- Add `@Version` fields to User and Settings entities for optimistic locking
- Fix ApiToken entity to include missing `revokedAt` field
- Complete all entity relationship mappings to match Django models exactly
2. **Maintain API Compatibility**: All existing API endpoints must work identically
3. **Database Schema**: Must match Django structure for seamless migration
4. **Security**: Implement robust security from day one
5. **Testing**: Comprehensive testing is mandatory
6. **Documentation**: Provide clear setup and development guides
7. **Extensibility**: Design for future enhancements and scaling

## Success Criteria - Business & Technical Excellence

### Business Success Metrics
The implementation must deliver measurable business outcomes:

**User Experience & Growth:**
- **Performance Target**: < 2 second average response time for image processing (95th percentile) to meet Student Sarah's instant help needs
- **Accuracy Standard**: > 95% accuracy rate for mathematical solutions to maintainEducator Emma's trust
- **Scalability Goal**: Support 10,000+ concurrent users to meet growth projections
- **System Reliability**: 99.9% uptime (maximum 43 minutes downtime/month) for all user personas

**Technical Excellence Indicators:**
- **Database Performance**: < 100ms query response time (95th percentile) for smooth user experience
- **API Reliability**: < 1% error rate across all endpoints to maintain Developer David's confidence
- **Cache Performance**: > 90% cache hit rate for optimal response times
- **Security Compliance**: Zero critical security vulnerabilities to protect all user data

### Technical Implementation Success
The implementation is successful when:

**Functional Excellence:**
1. **100% API Compatibility**: All Django functionality replicated with identical responses
2. **Database Integrity**: Schema matches existing structure with seamless migration capability
3. **Security Robustness**: Multi-modal authentication properly implemented for all user types
4. **Performance Standards**: Sub-2 second response times achieved consistently
5. **Scalability Architecture**: System handles projected 10x user growth without degradation

**Operational Excellence:**
6. **Development Environment**: Smooth Docker Compose setup for efficient development workflow
7. **Testing Coverage**: > 80% code coverage with critical paths 100% covered
8. **Documentation Quality**: Comprehensive documentation enabling easy team onboarding
9. **Code Standards**: Enterprise-grade code quality with proper design patterns
10. **Monitoring Capability**: Complete observability stack for production readiness

**Business Value Delivery:**
11. **User Experience**: Seamless experience across all user personas (Student, Educator, Developer, Admin)
12. **Cost Efficiency**: Optimized resource usage supporting sustainable business model
13. **Market Readiness**: Platform ready to compete effectively in educational technology market
14. **Future Extensibility**: Architecture supports planned feature enhancements and market expansion

### Quality Assurance - Business Impact Focus

**Enhanced Quality Checklist with Business Metrics:**

**User Experience Validation:**
- [✓] Response times < 2 seconds meet Student Sarah's instant help expectations
- [✓] 95%+ accuracy rate satisfies Educator Emma's reliability requirements
- [✓] Mobile-friendly endpoints support Student Sarah's multi-device usage
- [✓] Error handling provides clear guidance for all user types

**Developer Experience Excellence:**
- [✓] API documentation completeness enables Developer David's integration needs
- [✓] Consistent response format supports reliable application development
- [✓] OpenAPI 3.0 documentation provides comprehensive integration guidance
- [✓] Error codes and messages support effective debugging and troubleshooting

**Administrative Capability:**
- [✓] Admin interface supports Admin Alex's system management requirements
- [✓] User management tools enable effective account oversight
- [✓] Billing administration supports revenue tracking and management
- [✓] System monitoring provides real-time health insights

**Business Metric Alignment:**
- [✓] Performance targets support 10,000+ MAU growth goal
- [✓] Reliability standards enable 99.9% uptime achievement
- [✓] Scalability architecture supports business growth projections
- [✓] Cost optimization supports sustainable revenue model

## Strategic Implementation Guidance

This enhanced prompt provides comprehensive guidance that bridges technical requirements with business objectives. The implementation must deliver both technical excellence and measurable business value. **You must strictly follow `@JAVA_TECHNICAL_SPECIFICATION.md`** as your primary reference document throughout the implementation.

**Key Success Principles:**
1. **User-Centric Design**: Every technical decision should enhance the experience for our target personas
2. **Business Value Focus**: Architecture decisions must support growth, reliability, and cost-effectiveness
3. **Market Competitiveness**: Implementation should position us as the leading AI-powered mathematical problem-solving platform
4. **Future Readiness**: System architecture must support planned expansion into adjacent markets and features

All requirements must be met with high-quality, maintainable code that ensures 100% functional compatibility with the existing Django backend while delivering the business value needed to achieve our strategic objectives.
