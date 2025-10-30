# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Application Lifecycle
- `./gradlew bootRun` - Start the Spring Boot application in development mode
- `./gradlew bootBuildImage` - Build Docker container image
- `./gradlew build` - Build the application (compile + test + quality checks)
- `./gradlew clean` - Clean build artifacts

### Testing
- `./gradlew test` - Run all tests with JUnit 5
- `./gradlew test --tests "ClassName"` - Run single test class
- `./gradlew test --tests "com.trc.platform.users.*"` - Run tests for specific package
- `./gradlew jacocoTestReport` - Generate code coverage report after tests
- `./gradlew jacocoTestCoverageVerification` - Verify minimum 70% code coverage

### Code Quality (All Integrated into `./gradlew check`)
- `./gradlew check` - Run all quality checks (PMD, SpotBugs, Checkstyle, JaCoCo)
- `./gradlew spotlessApply` - Auto-format code using Google Java Style
- `./gradlew spotlessCheck` - Check if code is properly formatted
- `./gradlew spotbugsMain` - Run SpotBugs static analysis
- `./gradlew pmdMain` - Run PMD static analysis
- `./gradlew checkstyleMain` - Run Checkstyle verification
- `./gradlew generateLicenseReport` - Generate dependency license compliance report
- `./gradlew dependencyCheckAnalyze` - Run OWASP security vulnerability scanning
- `./gradlew sonar` - Analyze with SonarQube (requires configuration)

### Database
- Database migrations are handled by Flyway automatically on startup
- Migration files: `src/main/resources/db/migration/`
- Test database uses TestContainers for integration testing

## Architecture Overview

### Domain Structure
The application follows **domain-driven design** with clear bounded contexts:

- **users** (`com.trc.platform.users`) - User authentication, registration, API tokens
- **core** (`com.trc.platform.core`) - Mathematical problem solving with OpenAI integration
- **usage** (`com.trc.platform.usage`) - Usage tracking, billing periods, cost management
- **admin** (`com.trc.platform.admin`) - Administrative functions (invite codes, billing management)
- **security** (`com.trc.platform.security`) - JWT and API token authentication
- **config** (`com.trc.platform.config`) - Application settings and infrastructure config

### Specialized Sub-Agents
The project includes specialized Claude sub-agents for expert guidance:

#### Available Agents
1. **Test Coverage Architect** (`.claude/agents/test-coverage-architect.md`)
   - Designs comprehensive testing strategies
   - Focuses on unit, integration, and contract testing
   - Ensures >90% coverage for business logic
   - Validates billing calculations and security paths

2. **Security Reviewer** (`.claude/agents/security-reviewer.md`)
   - Validates authentication and authorization
   - Reviews data protection and input validation
   - Audits external integration security
   - Ensures compliance with security best practices

3. **Billing Accuracy Validator** (`.claude/agents/billing-accuracy-validator.md`)
   - Validates 100% billing calculation accuracy
   - Tests edge cases and financial precision
   - Ensures audit trail completeness
   - Verifies cost calculation algorithms

4. **Performance Optimizer** (`.claude/agents/performance-optimizer.md`)
   - Identifies and resolves performance bottlenecks
   - Optimizes OpenAI API integration
   - Enhances database and caching strategies
   - Implements load testing and monitoring

5. **API Documentation Specialist** (`.claude/agents/api-documentation-specialist.md`)
   - Maintains comprehensive API documentation
   - Generates OpenAPI specifications
   - Creates client integration examples
   - Ensures documentation accuracy and completeness

### Key Architectural Patterns

#### Security Architecture
- **Multi-layered authentication**: JWT tokens for web + API tokens for programmatic access
- **Stateless design**: No server-side sessions, all authentication token-based
- **Role-based access**: Admin endpoints protected with `@PreAuthorize("hasRole('ADMIN')")`
- **Password hashing**: Argon2 for secure password storage

#### Database Design
- **Primary keys**: UUID-based using Hibernate `@UUIDGenerator`
- **Optimistic locking**: `@Version` for concurrency control
- **Soft deletion**: Logical deletion patterns where applicable
- **Performance**: Strategic indexing and HikariCP connection pooling
- **Timezone handling**: All timestamps stored as UTC using `TIMESTAMP WITH TIME ZONE`

#### Timezone Configuration
- **Database**: All timestamp columns use `TIMESTAMP WITH TIME ZONE` (timestamptz)
- **JPA**: Configured with `hibernate.jdbc.time_zone: UTC` for automatic conversion
- **Application code**: Use `LocalDateTime.now()` - JPA handles UTC conversion automatically
- **API responses**: Timestamps are returned in ISO format with timezone information

#### External Integrations
- **OpenAI API**: Mathematical problem solving via `CoreProcessingService`
- **Email Service**: User verification and notifications
- **Reactive HTTP**: `WebClient` for non-blocking external calls

#### Caching Strategy
- **Multi-level**: L1 Caffeine (in-memory) + L2 Redis (distributed)
- **Cache-aside**: Services manage cache invalidation explicitly
- **TTL-based**: Configurable expiration times

### Key Services and Relationships

#### Core Business Flow
```
User Request → Authentication Filter → Controller → Service → Repository
                                     ↓
                              Usage Logging → Billing Calculation
```

#### Authentication Flow
```
Request → JWT Filter → API Token Filter → Security Context → Controller
```

#### Key Service Dependencies
- `CoreProcessingService` - OpenAI integration for math solving
- `AuthenticationService` - JWT token generation and validation
- `BillingService` - Usage-based billing calculations
- `EmailService` - Transactional email sending
- `ApiTokenService` - Programmatic access token management

## Environment Configuration

### Required Environment Variables
- `DATABASE_URL` - PostgreSQL connection URL (default: localhost:5432/trc_platform)
- `DATABASE_USERNAME` - Database username (default: trc_user)
- `DATABASE_PASSWORD` - Database password (default: trc_password)
- `OPENAI_API_KEY` - OpenAI API key for math solving
- `JWT_SECRET` - Secret key for JWT token signing
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USERNAME`, `EMAIL_PASSWORD` - SMTP configuration

### Configuration Files
- `application.yml` - Base configuration
- `application-dev.yml` - Development environment overrides
- `application-prod.yml` - Production environment overrides
- `application-test.yml` - Test environment configuration

## Code Quality Standards

### Quality Tools Configuration
- **Spotless**: Google Java Format v1.22.0 with automatic import cleanup
- **JaCoCo**: Minimum 70% code coverage requirement
- **PMD**: Custom ruleset in `config/pmd/ruleset.xml`
- **SpotBugs**: Maximum effort, low report level with exclusions in `config/spotbugs/exclude.xml`
- **Checkstyle**: 120-character line limit with comprehensive style rules
- **ErrorProne**: Compile-time error detection enabled
- **OWASP Dependency Check**: Security scanning with CVSS ≥ 7.0 failure threshold

### Project-Specific Rules
The project includes specialized rules in `.claude/rules/`:

1. **Security Rules** (`.claude/rules/security-rules.md`)
   - Authentication and authorization requirements
   - Data protection and validation standards
   - Network and configuration security
   - Database and API security patterns

2. **Performance Rules** (`.claude/rules/performance-rules.md`)
   - Reactive programming requirements
   - Database optimization and indexing
   - Caching strategies and memory management
   - Monitoring and alerting standards

3. **Quality Rules** (`.claude/rules/quality-rules.md`)
   - Testing coverage and quality gates
   - Error handling and documentation standards
   - Business logic validation requirements
   - Code review and integration testing

### Development Templates
The project includes code templates in `.claude/templates/` for consistent development patterns:

### Available Templates
- **Controller Template**: REST controller with OpenAPI documentation
- **Service Template**: Service layer with transaction management
- **Repository Template**: JPA repository with common query patterns
- **Entity Template**: JPA entity with audit fields
- **DTO Templates**: Request/response DTOs with validation
- **Exception Template**: Custom exceptions with proper HTTP status

### Template Usage
1. Copy templates to your package structure
2. Replace placeholders (`${EntityName}`, `${domain}`, etc.)
3. Customize for your specific requirements
4. Templates integrate with all quality tools automatically

### Code Standards
- All new code must pass `./gradlew check` (includes all quality tools)
- Use constructor injection for dependencies
- Follow Google Java Style Guide (enforced by Spotless)
- Write tests for business logic - JaCoCo coverage is verified
- Handle errors gracefully with custom exceptions

## API Structure

### REST Endpoints
- `/api/customers/` - User management (register, login, profile)
- `/api/core/` - Core functionality (solve math problems, health check)
- `/api/usage/` - Usage and billing information
- `/api/v1/admin/` - Administrative functions (admin-only access)

### Authentication
- **JWT Authentication**: Include `Authorization: Bearer <token>` header
- **API Token Authentication**: Include `X-API-Key: <token>` header
- **Public endpoints**: Registration, login, health checks

## Development Workflow

### Making Changes
1. Create feature branch from main
2. Make code changes
3. Run `./gradlew spotlessApply` to format code
4. Run `./gradlew check` to verify quality and run tests
5. Fix any failing tests or quality violations
6. Commit changes (quality gates enforced by build)
7. Create pull request for review

### Quality Gates
The build will fail if:
- Tests fail or don't meet 70% coverage requirement
- Code style violations exist (Checkstyle)
- SpotBugs finds critical issues
- PMD rule violations exist
- Code is not properly formatted (Spotless)
- Security vulnerabilities found in dependencies (OWASP)

### Reports Location
After running quality checks, view reports in:
- `build/reports/jacoco/` - Code coverage
- `build/reports/spotbugs/` - Static analysis findings
- `build/reports/pmd/` - PMD violations
- `build/reports/checkstyle/` - Style violations
- `build/reports/dependency-license/` - License compliance

Additional Rules:
1. First think through the problem, read the codebase for relevant files, and write a plan to tasks/todo.md.
2. The plan should have a list of todo items that you can check off as you complete them
3. Before you begin working, check in with me and I will verify the plan.
4. Then, begin working on the todo items, marking them as complete as you go.
5. Please every step of the way just give me a high level explanation of what changes you made
6. Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
7. Finally, add a review section to the todo.md file with a summary of the changes you made and any other relevant information.
8. DO NOT BE LAZY. NEVER BE LAZY. IF THERE IS A BUG FIND THE ROOT CAUSE AND FIX IT. NO TEMPORARY FIXES. YOU ARE A SENIOR DEVELOPER. NEVER BE LAZY
9. MAKE ALL FIXES AND CODE CHANGES AS SIMPLE AS HUMANLY POSSIBLE. THEY SHOULD ONLY IMPACT NECESSARY CODE RELEVANT TO THE TASK AND NOTHING ELSE. IT SHOULD IMPACT AS LITTLE CODE AS POSSIBLE. YOUR GOAL IS TO NOT INTRODUCE ANY BUGS. IT'S ALL ABOUT SIMPLICITY

CRITICAL: When debugging, you MUST trace through the ENTIRE code flow step by step. No assumptions. No shortcuts.
