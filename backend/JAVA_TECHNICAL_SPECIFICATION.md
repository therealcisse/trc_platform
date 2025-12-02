# TRC Platform Java Backend Technical Specification

## Executive Summary

This document provides a comprehensive technical specification for rewriting the existing Django-based TRC Platform backend in Java using modern enterprise-grade frameworks and best practices. The specification covers architecture, technology stack, API design, data models, security, and implementation guidelines.

*Note: For complete deployment architecture and Kubernetes instructions, see [JAVA_TECHNICAL_SPECIFICATION_K8S.md](JAVA_TECHNICAL_SPECIFICATION_K8S.md).*

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Design](#architecture-design)
4. [Data Model Specification](#data-model-specification)
5. [API Specification](#api-specification)
6. [Security Architecture](#security-architecture)
7. [Performance & Caching Strategy](#performance--caching-strategy)
8. [Development Guidelines](#development-guidelines)
9. [Testing Strategy](#testing-strategy)
10. [Database Migration Strategy](#database-migration-strategy)
11. [Monitoring & Observability](#monitoring--observability)

*Note: For Kubernetes deployment instructions, see [JAVA_TECHNICAL_SPECIFICATION_K8S.md](JAVA_TECHNICAL_SPECIFICATION_K8S.md)*

---

## 1. Project Overview

### 1.1 Current System Analysis

The existing Django backend provides:

- **User Management**: Registration, authentication, email verification
- **Image Processing**: AI-powered math problem solving using OpenAI Vision API
- **Usage Tracking**: Request logging, billing periods, cost calculation
- **API Management**: Token-based authentication for programmatic access
- **Email Services**: Verification emails, notifications using Resend SMTP

### 1.2 Business Requirements

- Maintain 100% functional compatibility with existing API endpoints
- Improve performance and scalability
- Enhance security posture with modern Java security practices
- Ensure high availability and fault tolerance
- Provide comprehensive monitoring and observability

### 1.3 Technical Goals

- **Framework**: Spring Boot 3.x with Java 21+
- **Architecture**: Microservices with modular monolith approach
- **Database**: PostgreSQL with JPA/Hibernate
- **Caching**: Redis with Spring Cache abstraction
- **Security**: Spring Security with JWT and OAuth2
- **API Documentation**: OpenAPI 3.0 with SpringDoc

---

## 2. Technology Stack

### 2.1 Core Framework

**Primary Choice: Spring Boot 3.3.x**

**Rationale:**
- Mature ecosystem with extensive enterprise adoption
- Comprehensive security features (Spring Security)
- Excellent integration with databases and messaging systems
- Strong community support and documentation
- Built-in production-ready features (actuator, metrics)

**Alternative Considered: Quarkus**
- Better startup time and memory usage
- Excellent for serverless and cloud-native scenarios
- Smaller ecosystem compared to Spring Boot

**Decision**: Spring Boot provides better long-term maintainability and ecosystem support for enterprise requirements.

### 2.2 Technology Components

| Component | Technology | Version | Justification |
|-----------|------------|---------|---------------|
| **Language** | Java | 21 LTS | Latest LTS with modern features (virtual threads, records) |
| **Framework** | Spring Boot | 3.3.x | Current stable version with Jakarta EE |
| **Security** | Spring Security | 6.3.x | Comprehensive security framework |
| **Database** | PostgreSQL | 16+ | Robust RDBMS with advanced features |
| **ORM** | Spring Data JPA/Hibernate | 3.2.x | Mature ORM with caching capabilities |
| **Validation** | Jakarta Bean Validation | 3.0.x | Standard validation framework |
| **Caching** | Spring Cache + Caffeine/Redis | 3.2.x | Dual caching: Memory (default) + Redis (optional) |
| **HTTP Client** | WebClient (Spring WebFlux) | 6.1.x | Non-blocking HTTP client for OpenAI API |
| **Settings Management** | Custom Singleton Service | Built-in | Database-backed settings with caching |
| **Testing** | JUnit 5 + Testcontainers | 5.10.x | Modern testing with integration support |
| **Documentation** | SpringDoc OpenAPI | 2.5.x | Automatic API documentation |
| **Build** | Maven | 3.9.x | Mature build tool with dependency management |

*Note: For containerization and orchestration details, see [JAVA_TECHNICAL_SPECIFICATION_K8S.md](JAVA_TECHNICAL_SPECIFICATION_K8S.md)*

### 2.3 External Service Integrations

| Service | Integration Method | Library |
|---------|-------------------|---------|
| **OpenAI API** | HTTP Client (WebClient) | Spring WebFlux |
| **Email Service (Resend)** | SMTP Client | Spring Mail |
| **Monitoring** | Micrometer + Prometheus | Spring Boot Actuator |
| **Logging** | Logback + ELK Stack | Spring Boot Default |

---

## 3. Architecture Design

### 3.1 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend SPA  │────│  API Gateway    │────│   Load Balancer │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │  Spring Boot App    │
                    │  (Modular Design)   │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌───────▼────────┐
│  User Module   │   │  Core Module      │   │  Usage Module  │
│                │   │                   │   │                │
│ • Auth         │   │ • Image Processing│   │ • Billing      │
│ • Profile      │   │ • OpenAI Client   │   │ • Analytics    │
│ • API Tokens   │   │ • File Handling   │   │ • Reporting    │
└────────────────┘   └───────────────────┘   └────────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌───────▼────────┐
│   PostgreSQL   │   │      Redis        │   │ External APIs  │
│   (Primary DB) │   │     (Cache)       │   │   (OpenAI)     │
└────────────────┘   └───────────────────┘   └────────────────┘
```

### 3.2 Module Structure

**Package Organization:**
```
com.trc.platform/
├── config/                 # Configuration classes
├── common/                 # Shared utilities, constants, exceptions
├── security/               # Security configuration and components
├── users/                  # User management module
│   ├── controller/        # REST controllers
│   ├── service/           # Business logic
│   ├── repository/         # Data access layer
│   ├── dto/               # Data transfer objects
│   └── entity/            # JPA entities
├── core/                   # Core business functionality
│   ├── controller/
│   ├── service/
│   ├── repository/
│   ├── dto/
│   └── entity/
├── usage/                  # Usage tracking and billing
│   ├── controller/
│   ├── service/
│   ├── repository/
│   ├── dto/
│   └── entity/
└── monitoring/             # Health checks and metrics
```

### 3.3 Layer Architecture

**Each module follows the layered architecture pattern:**

```
┌────────────────────────────────────────────────────────────────┐
│                    Presentation Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Controllers   │  │   DTOs          │  │   Validation    │ │
│  │   (REST APIs)   │  │   (Request/     │  │   (Bean         │ │
│  │                 │  │   Response)     │  │   Validation)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────┐
│                    Business Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Services      │  │   Domain        │  │   Business      │ │
│  │   (Logic)       │  │   Models        │  │   Rules         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Repositories  │  │   Entities      │  │   Database      │ │
│  │   (JPA)         │  │   (ORM)         │  │   (PostgreSQL)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Data Model Specification

### 4.1 Database Schema Design

**Entity Relationship Overview:**
```
User (1) ──────── (N) BillingPeriod
User (1) ──────── (N) RequestLog
User (1) ──────── (N) ApiToken
User (1) ──────── (N) InviteCode
ApiToken (1) ───── (N) RequestLog
BillingPeriod (1) ─ (N) RequestLog
```

### 4.2 Entity Definitions

#### 4.2.1 User Entity

```java
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = false)
    private String passwordHash;

    @Column(name = "is_active", nullable = false)
    private Boolean active = true;

    @Column(name = "is_staff", nullable = false)
    private Boolean staff = false;

    @Column(name = "email_verified_at")
    private LocalDateTime emailVerifiedAt;

    @Column(name = "date_joined", nullable = false)
    private LocalDateTime dateJoined;

    @Column(name = "user_accepted_terms", nullable = false)
    private Boolean acceptedTerms = false;

    @Column(name = "user_acknowledged_disclaimer", nullable = false)
    private Boolean acknowledgedDisclaimer = false;

    @Version
    private Long version;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<ApiToken> apiTokens = new HashSet<>();

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<BillingPeriod> billingPeriods = new HashSet<>();

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<RequestLog> requestLogs = new HashSet<>();
}
```

#### 4.2.2 ApiToken Entity

```java
@Entity
@Table(name = "api_tokens")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ApiToken {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "token_hash", unique = true, nullable = false)
    private String tokenHash;

    @Column(name = "token_prefix", nullable = false)
    private String tokenPrefix;

    @Column(name = "name", nullable = false)
    private String name;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "last_used_at")
    private LocalDateTime lastUsedAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "is_active", nullable = false)
    private Boolean active = true;

    @Column(name = "usage_count", nullable = false)
    private Long usageCount = 0L;

    @OneToMany(mappedBy = "token", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<RequestLog> requestLogs = new HashSet<>();
}
```

#### 4.2.3 BillingPeriod Entity

```java
@Entity
@Table(name = "billing_periods", indexes = {
    @Index(name = "idx_user_period", columnList = "user_id, period_start"),
    @Index(name = "idx_current_period", columnList = "is_current")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BillingPeriod {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "period_start", nullable = false)
    private LocalDate periodStart;

    @Column(name = "period_end", nullable = false)
    private LocalDate periodEnd;

    @Column(name = "total_requests", nullable = false)
    private Integer totalRequests = 0;

    @Column(name = "total_cost_cents", nullable = false)
    private Integer totalCostCents = 0;

    @Column(name = "is_current", nullable = false)
    private Boolean current = false;

    @Enumerated(EnumType.STRING)
    @Column(name = "payment_status", nullable = false)
    private PaymentStatus paymentStatus = PaymentStatus.PENDING;

    @Version
    private Long version;

    @OneToMany(mappedBy = "billingPeriod", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private Set<RequestLog> requests = new HashSet<>();

    public enum PaymentStatus {
        PENDING, PAID, OVERDUE, WAIVED
    }
}
```

#### 4.2.4 RequestLog Entity

```java
@Entity
@Table(name = "request_logs", indexes = {
    @Index(name = "idx_user_timestamp", columnList = "user_id, request_ts"),
    @Index(name = "idx_request_ts", columnList = "request_ts"),
    @Index(name = "idx_request_id", columnList = "request_id"),
    @Index(name = "idx_flow_id", columnList = "flow_id")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RequestLog {

    @Id
    @GeneratedValue(generator = "UUID")
    @GenericGenerator(name = "UUID", strategy = "org.hibernate.id.UUIDGenerator")
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "token_id")
    private ApiToken token;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "billing_period_id")
    private BillingPeriod billingPeriod;

    @Column(name = "service", nullable = false)
    private String service = "core.image_solve";

    @Column(name = "request_ts", nullable = false)
    private LocalDateTime requestTs;

    @Column(name = "duration_ms", nullable = false)
    private Integer durationMs;

    @Column(name = "request_bytes", nullable = false)
    private Integer requestBytes;

    @Column(name = "response_bytes", nullable = false)
    private Integer responseBytes;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private RequestStatus status;

    @Column(name = "error_code", length = 50)
    private String errorCode;

    @Column(name = "request_id", nullable = false)
    private UUID requestId;

    @Column(name = "flow_id", length = 255)
    private String flowId;

    @Column(name = "result", columnDefinition = "TEXT")
    private String result;

    public enum RequestStatus {
        SUCCESS,
        ERROR
    }
}
```


#### 4.2.6 Settings Entity (Singleton Pattern)

```java
@Entity
@Table(name = "settings")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Settings {

    @Id
    @Column(name = "id", nullable = false)
    private Long id = 1L; // Fixed ID for singleton pattern

    @Column(name = "cost_per_request_cents", nullable = false)
    private Integer costPerRequestCents = 100;

    @Column(name = "openai_model")
    private String openaiModel = "gpt-4-vision-preview";

    @Column(name = "openai_timeout_s", nullable = false)
    private Integer openaiTimeoutSeconds = 30;

    @Column(name = "app_domain")
    @URL(message = "Invalid application domain URL")
    private String appDomain;


    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    @PrePersist
    protected void onCreate() {
        if (updatedAt == null) {
            updatedAt = LocalDateTime.now();
        }
    }
}
```

### 4.3 Database Configuration

```yaml
# application.yml
spring:
  datasource:
    url: ${DATABASE_URL:jdbc:postgresql://localhost:5432/trc_platform}
    username: ${DATABASE_USERNAME:trc_user}
    password: ${DATABASE_PASSWORD:trc_password}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000
      max-lifetime: 600000
      connection-timeout: 30000
      leak-detection-threshold: 60000

  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
        jdbc:
          batch_size: 20
        order_inserts: true
        order_updates: true
        batch_versioned_data: true

  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    validate-on-migrate: true
```

---

## 5. API Specification

### 5.1 API Design Principles

- **RESTful Design**: Follow REST conventions and HTTP semantics
- **Versioning**: URL-based versioning (`/api/v1/`)
- **Consistent Responses**: Standard response format across all endpoints
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **Security**: All endpoints except public ones require authentication
- **Documentation**: Auto-generated OpenAPI 3.0 documentation

### 5.2 Common Response Format

```java
@Data
@Builder
public class ApiResponse<T> {
    private Boolean success;
    private T data;
    private String message;
    private String errorCode;
    private LocalDateTime timestamp;

    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder()
            .success(true)
            .data(data)
            .timestamp(LocalDateTime.now())
            .build();
    }

    public static <T> ApiResponse<T> error(String message, String errorCode) {
        return ApiResponse.<T>builder()
            .success(false)
            .message(message)
            .error(error)
            .timestamp(LocalDateTime.now())
            .build();
    }
}
```

### 5.3 Authentication Endpoints

#### 5.3.1 User Registration

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "acceptedTerms": true,
  "acknowledgedDisclaimer": true
}

Response 201:
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "emailVerified": false,
      "dateJoined": "2025-01-01T00:00:00Z"
    },
    "message": "Registration successful. Please check your email for verification."
  }
}
```

#### 5.3.2 User Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response 200:
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "emailVerified": true
    },
    "sessionToken": "session_token_here"
  }
}
```

### 5.4 User Management Endpoints

#### 5.4.1 Get Current User Profile

```http
GET /api/v1/users/me
Authorization: Bearer {session_token}

Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "emailVerified": true,
    "dateJoined": "2025-01-01T00:00:00Z",
    "acceptedTerms": true,
    "acknowledgedDisclaimer": true
  }
}
```

#### 5.4.2 API Token Management

```http
GET /api/v1/users/tokens
Authorization: Bearer {session_token}

Response 200:
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Production API Token",
      "tokenPrefix": "tok_abcdef12",
      "createdAt": "2025-01-01T00:00:00Z",
      "lastUsedAt": "2025-01-02T12:34:56Z",
      "usageCount": 42,
      "active": true
    }
  ]
}

POST /api/v1/users/tokens
Authorization: Bearer {session_token}
Content-Type: application/json

{
  "name": "New API Token"
}

Response 201:
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "New API Token",
    "token": "tok_ghijkl34_full_token_here",
    "tokenPrefix": "tok_ghijkl34",
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

### 5.5 Core Processing Endpoints

#### 5.5.1 Math Problem Solving (Solve)

```http
POST /api/v1/core/solve
Authorization: Bearer {api_token}
Content-Type: multipart/form-data

image: [binary_image_data]
flow: "math_solving" (optional)
parameters: {} (optional JSON)

Response 200:
{
  "success": true,
  "data": {
    "result": "42",
    "confidence": 0.95,
    "processingTime": 1250,
    "requestId": "uuid"
  }
}

Response 400 (Error):
{
  "success": false,
  "message": "Invalid image format",
  "errorCode": "INVALID_IMAGE_FORMAT"
}
```

#### 5.5.2 Health Check

```http
GET /api/v1/core/health

Response 200:
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-01T00:00:00Z",
    "version": "1.0.0",
    "checks": {
      "database": "healthy",
      "redis": "healthy",
      "openai": "healthy"
    }
  }
}
```

### 5.6 Usage and Billing Endpoints

#### 5.6.1 Usage Summary

```http
GET /api/v1/usage/summary?period=current
Authorization: Bearer {session_token}

Response 200:
{
  "success": true,
  "data": {
    "period": {
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "totalRequests": 150,
    "totalCost": 15.00,
    "averageCostPerRequest": 0.10
  }
}
```

#### 5.6.2 Request History

```http
GET /api/v1/usage/requests?page=0&size=20&sort=createdAt,desc
Authorization: Bearer {session_token}

Response 200:
{
  "success": true,
  "data": {
    "content": [
      {
        "id": "uuid",
        "createdAt": "2025-01-01T12:00:00Z",
        "processingTime": 1250,
        "statusCode": 200,
        "cost": 0.10,
        "hasImage": true
      }
    ],
    "page": 0,
    "size": 20,
    "totalElements": 150,
    "totalPages": 8
  }
}
```

### 5.7 Settings Management Endpoints

#### 5.7.1 Get Application Settings

```http
GET /api/v1/admin/settings
Authorization: Bearer {admin_token}

Response 200:
{
  "success": true,
  "data": {
    "id": 1,
    "costPerRequestCents": 100,
    "openaiModel": "gpt-4-vision-preview",
    "openaiTimeoutSeconds": 30,
    "appDomain": "https://app.trc-platform.com",
    "updatedAt": "2025-01-01T12:00:00Z"
  }
}
```

#### 5.7.2 Update Application Settings

```http
PUT /api/v1/admin/settings
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "costPerRequestCents": 150,
  "openaiModel": "gpt-4-vision-preview",
  "openaiTimeoutSeconds": 45,
  "appDomain": "https://app.trc-platform.com",
  "saveRequestImages": true,
  "maxSavedImageSizeMb": 15,
  "imageRetentionDays": 60
}

Response 200:
{
  "success": true,
  "data": {
    "id": 1,
    "costPerRequestCents": 150,
    "openaiModel": "gpt-4-vision-preview",
    "openaiTimeoutSeconds": 45,
    "appDomain": "https://app.trc-platform.com",
    "updatedAt": "2025-01-01T12:30:00Z"
  }
}
```

---

## 6. Security Architecture

### 6.1 Authentication Strategy

#### 6.1.1 Multi-Modal Authentication

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(authz -> authz
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/api/v1/core/health").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/api/v1/core/solve").hasRole("USER")
                .requestMatchers("/api/v1/users/**").hasRole("USER")
                .requestMatchers("/api/v1/usage/**").hasRole("USER")
                .anyRequest().authenticated())
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class)
            .addFilterBefore(apiTokenAuthenticationFilter(), JwtAuthenticationFilter.class)
            .exceptionHandling(exceptions -> exceptions
                .authenticationEntryPoint(unauthorizedHandler()))
            .build();
    }
}
```

#### 6.1.2 Session Authentication (Web Interface)

```java
@Service
public class SessionAuthenticationService {

    public AuthResponse authenticate(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
            .orElseThrow(() -> new AuthenticationException("Invalid credentials"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new AuthenticationException("Invalid credentials");
        }

        if (!user.isActive()) {
            throw new AuthenticationException("Account is disabled");
        }

        // Generate session token
        String sessionToken = generateSessionToken(user);

        return AuthResponse.builder()
            .user(UserDto.from(user))
            .sessionToken(sessionToken)
            .build();
    }

    private String generateSessionToken(User user) {
        return Jwts.builder()
            .setSubject(user.getId().toString())
            .setIssuedAt(new Date())
            .setExpiration(Date.from(LocalDateTime.now().plusHours(24).toInstant(ZoneOffset.UTC)))
            .signWith(getSignInKey(), SignatureAlgorithm.HS256)
            .compact();
    }
}
```

#### 6.1.3 API Token Authentication

```java
@Component
public class ApiTokenAuthenticationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                  HttpServletResponse response,
                                  FilterChain filterChain) throws ServletException, IOException {

        String token = extractToken(request);
        if (token != null) {
            try {
                Authentication auth = authenticateToken(token);
                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (ApiTokenException e) {
                // Log invalid token attempts
                log.warn("Invalid API token attempt: {}", e.getMessage());
            }
        }

        filterChain.doFilter(request, response);
    }

    private Authentication authenticateToken(String token) {
        // Find token by hash
        ApiToken apiToken = apiTokenRepository.findByTokenHash(hashToken(token))
            .orElseThrow(() -> new ApiTokenException("Invalid token"));

        if (!apiToken.isActive() || apiToken.isExpired()) {
            throw new ApiTokenException("Token inactive or expired");
        }

        // Update usage statistics
        apiToken.setLastUsedAt(LocalDateTime.now());
        apiToken.setUsageCount(apiToken.getUsageCount() + 1);
        apiTokenRepository.save(apiToken);

        // Create authentication
        UserPrincipal principal = new UserPrincipal(apiToken.getUser());
        return new UsernamePasswordAuthenticationToken(principal, null, principal.getAuthorities());
    }
}
```

### 6.2 Authorization Framework

#### 6.2.1 Role-Based Access Control

```java
public enum Role {
    USER(Set.of(
        Permission.PROCESS_IMAGES,
        Permission.VIEW_OWN_USAGE,
        Permission.MANAGE_API_TOKENS
    )),
    ADMIN(Set.of(
        Permission.PROCESS_IMAGES,
        Permission.VIEW_OWN_USAGE,
        Permission.MANAGE_API_TOKENS,
        Permission.VIEW_ALL_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_SYSTEM_METRICS
    ));

    private final Set<Permission> permissions;

    Role(Set<Permission> permissions) {
        this.permissions = permissions;
    }

    public boolean hasPermission(Permission permission) {
        return permissions.contains(permission);
    }
}

public enum Permission {
    PROCESS_IMAGES,
    VIEW_OWN_USAGE,
    MANAGE_API_TOKENS,
    VIEW_ALL_USERS,
    MANAGE_USERS,
    VIEW_SYSTEM_METRICS
}
```

#### 6.2.2 Method-Level Security

```java
@RestController
@RequestMapping("/api/v1/users")
@PreAuthorize("hasRole('USER')")
public class UserController {

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<UserDto>> getCurrentUser(@AuthenticationPrincipal UserPrincipal user) {
        return ResponseEntity.ok(ApiResponse.success(UserDto.from(user.getUser())));
    }

    @PostMapping("/tokens")
    @PreAuthorize("hasPermission('MANAGE_API_TOKENS')")
    public ResponseEntity<ApiResponse<ApiTokenDto>> createToken(
            @Valid @RequestBody CreateTokenRequest request,
            @AuthenticationPrincipal UserPrincipal user) {
        ApiToken token = apiTokenService.createToken(user.getUser(), request);
        return ResponseEntity.ok(ApiResponse.success(ApiTokenDto.from(token)));
    }

    @GetMapping("/tokens")
    @PreAuthorize("hasPermission('MANAGE_API_TOKENS')")
    public ResponseEntity<ApiResponse<Page<ApiTokenDto>>> getTokens(
            @PageableDefault(size = 20) Pageable pageable,
            @AuthenticationPrincipal UserPrincipal user) {
        Page<ApiToken> tokens = apiTokenService.getUserTokens(user.getUser(), pageable);
        return ResponseEntity.ok(ApiResponse.success(tokens.map(ApiTokenDto::from)));
    }
}

@RestController
@RequestMapping("/api/v1/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminController {

    @Autowired
    private SettingsService settingsService;

    @GetMapping("/settings")
    public ResponseEntity<ApiResponse<SettingsDto>> getSettings() {
        Settings settings = settingsService.getSettings();
        return ResponseEntity.ok(ApiResponse.success(SettingsDto.from(settings)));
    }

    @PutMapping("/settings")
    @PreAuthorize("hasPermission('MANAGE_SETTINGS')")
    public ResponseEntity<ApiResponse<SettingsDto>> updateSettings(
            @Valid @RequestBody SettingsUpdateRequest request) {
        Settings updated = settingsService.updateSettings(request.toSettings());
        return ResponseEntity.ok(ApiResponse.success(SettingsDto.from(updated)));
    }

    @PostMapping("/settings/invalidate-cache")
    @PreAuthorize("hasPermission('MANAGE_SETTINGS')")
    public ResponseEntity<ApiResponse<Void>> invalidateSettingsCache() {
        settingsService.invalidateCache();
        return ResponseEntity.ok(ApiResponse.success(null));
    }
}
```

### 6.3 Input Validation and Sanitization

#### 6.3.1 Request Validation

```java
@Data
@Builder
public class LoginRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 255, message = "Email must be less than 255 characters")
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 128, message = "Password must be between 8 and 128 characters")
    @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]",
             message = "Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")
    private String password;
}

@Data
@Builder
public class RegistrationRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 255, message = "Email must be less than 255 characters")
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 8, max = 128, message = "Password must be between 8 and 128 characters")
    private String password;

    @NotNull(message = "Terms acceptance is required")
    private Boolean acceptedTerms;

    @NotNull(message = "Disclaimer acknowledgment is required")
    private Boolean acknowledgedDisclaimer;
}
```

### 6.4 Security Headers and CORS

```java
@Configuration
public class WebSecurityConfig {

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(Arrays.asList(
            "https://trc-platform.com",
            "https://app.trc-platform.com"
        ));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    @Bean
    public OncePerRequestFilter securityHeadersFilter() {
        return new OncePerRequestFilter() {
            @Override
            protected void doFilterInternal(HttpServletRequest request,
                                          HttpServletResponse response,
                                          FilterChain filterChain) throws ServletException, IOException {

                response.setHeader("X-Content-Type-Options", "nosniff");
                response.setHeader("X-Frame-Options", "DENY");
                response.setHeader("X-XSS-Protection", "1; mode=block");
                response.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
                response.setHeader("Content-Security-Policy",
                    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'");
                response.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");

                filterChain.doFilter(request, response);
            }
        };
    }
}
```

---

## 7. Performance & Caching Strategy

### 7.1 Dual Caching Architecture

#### 7.1.1 Cache Configuration with Memory and Redis Support

```java
@Configuration
@EnableCaching
public class CacheConfig {

    @Value("${app.cache.use-redis:false}")
    private boolean useRedisCache;

    @Bean
    @Primary
    public CacheManager cacheManager(RedisConnectionFactory redisConnectionFactory) {
        if (useRedisCache) {
            return redisCacheManager(redisConnectionFactory);
        } else {
            return caffeineCacheManager();
        }
    }

    @Bean("redisCacheManager")
    public CacheManager redisCacheManager(RedisConnectionFactory redisConnectionFactory) {
        Map<String, RedisCacheConfiguration> cacheConfigurations = new HashMap<>();

        // User cache - 1 hour TTL
        cacheConfigurations.put("users", RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofHours(1))
            .disableCachingNullValues());

        // API token cache - 30 minutes TTL
        cacheConfigurations.put("apiTokens", RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))
            .disableCachingNullValues());

        // Application settings cache - 5 minutes TTL (to ensure quick updates)
        cacheConfigurations.put("settings", RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(5))
            .disableCachingNullValues());

        // Flow-based response cache - 2 hours TTL
        cacheConfigurations.put("flowResponses", RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofHours(2))
            .disableCachingNullValues());

        return RedisCacheManager.builder(redisConnectionFactory)
            .withInitialCacheConfigurations(cacheConfigurations)
            .transactionAware()
            .build();
    }

    @Bean("caffeineCacheManager")
    public CacheManager caffeineCacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager();

        // Configure individual cache settings
        cacheManager.setCaffeine(Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofHours(1))
            .maximumSize(1000));

        return cacheManager;
    }

    @Bean
    public CacheKeyGenerator cacheKeyGenerator() {
        return (target, method, params) -> {
            StringBuilder sb = new StringBuilder();
            sb.append(target.getClass().getSimpleName()).append(".");
            sb.append(method.getName()).append(".");

            for (Object param : params) {
                if (param != null) {
                    sb.append(param.toString()).append(".");
                }
            }

            return sb.toString();
        };
    }
}
```

#### 7.1.2 Settings Cache Service

```java
@Service
@Slf4j
public class SettingsService {

    private final SettingsRepository settingsRepository;
    private final CacheManager cacheManager;
    private final ApplicationEventPublisher eventPublisher;

    @Autowired
    public SettingsService(SettingsRepository settingsRepository,
                       CacheManager cacheManager,
                       ApplicationEventPublisher eventPublisher) {
        this.settingsRepository = settingsRepository;
        this.cacheManager = cacheManager;
        this.eventPublisher = eventPublisher;
    }

    @Cacheable(value = "settings", key = "'app_settings'")
    public Settings getSettings() {
        return settingsRepository.findById(1L)
            .orElseGet(this::createDefaultSettings);
    }

    public Settings updateSettings(Settings newSettings) {
        Settings existing = getSettings();

        // Update fields
        BeanUtils.copyProperties(newSettings, existing, "id", "updatedAt");

        Settings updated = settingsRepository.save(existing);

        // Invalidate cache
        invalidateCache();

        // Publish settings updated event
        eventPublisher.publishEvent(new SettingsUpdatedEvent(updated));

        return updated;
    }

    public void invalidateCache() {
        Cache cache = cacheManager.getCache("settings");
        if (cache != null) {
            cache.evict("app_settings");
            log.info("Settings cache invalidated");
        }
    }

    @EventListener
    public void handleSettingsUpdated(SettingsUpdatedEvent event) {
        // Additional logic when settings are updated
        log.info("Settings updated: {}", event.getSettings());
    }

    private Settings createDefaultSettings() {
        Settings defaultSettings = Settings.builder()
            .id(1L)
            .costPerRequestCents(100)
            .openaiModel("gpt-4-vision-preview")
            .openaiTimeoutSeconds(30)
              .build();

        return settingsRepository.save(defaultSettings);
    }

    // Specific getter methods for common settings
    public String getOpenAiModel() {
        return getSettings().getOpenaiModel();
    }

    public int getOpenAiTimeoutSeconds() {
        return getSettings().getOpenaiTimeoutSeconds();
    }

    public int getCostPerRequestCents() {
        return getSettings().getCostPerRequestCents();
    }


    public String getAppDomain() {
        Settings settings = getSettings();
        return settings.getAppDomain() != null ? settings.getAppDomain() : "";
    }
}
```

#### 7.1.3 Application Configuration Properties

```yaml
# application.yml
spring:
  # Cache Configuration
  cache:
    type: ${SPRING_CACHE_TYPE:simple} # Will be overridden by @Primary CacheManager
    caffeine:
      spec: maximumSize=1000,expireAfterWrite=1h

  # Redis Configuration (optional)
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASSWORD:}
      timeout: 2000ms
      lettuce:
        pool:
          max-active: 8
          max-idle: 8
          min-idle: 0

# Application-specific cache configuration
app:
  cache:
    use-redis: ${USE_REDIS_CACHE:false}  # Enable Redis caching when true
    settings:
      ttl-minutes: 5  # Settings cache TTL
    users:
      ttl-hours: 1   # User cache TTL
    tokens:
      ttl-minutes: 30  # API token cache TTL
    flows:
      ttl-hours: 2   # Flow response cache TTL

# OpenAI Configuration (moved to settings)
openai:
  api-key: ${OPENAI_API_KEY:}
  base-url: https://api.openai.com/v1

# Email Configuration
mail:
  host: ${SMTP_HOST:smtp.resend.com}
  port: ${SMTP_PORT:587}
  username: ${RESEND_API_KEY:}
  password: ${RESEND_API_KEY:}
  from: ${DEFAULT_FROM_EMAIL:noreply@trc-platform.com}
```

#### 7.1.4 Application-Level Caching with Settings Integration

```java
@Service
public class UserService {

    @Cacheable(value = "users", key = "#userId")
    public UserDto getUserById(UUID userId) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException("User not found: " + userId));
        return UserDto.from(user);
    }

    @CacheEvict(value = "users", key = "#userId")
    public void evictUserCache(UUID userId) {
        log.debug("Evicted user cache for userId: {}", userId);
    }

    @Cacheable(value = "users", key = "#email")
    public UserDto getUserByEmail(String email) {
        User user = userRepository.findByEmail(email)
            .orElseThrow(() -> new UserNotFoundException("User not found: " + email));
        return UserDto.from(user);
    }
}

@Service
public class ApiTokenService {

    @Cacheable(value = "apiTokens", key = "#tokenHash")
    public Optional<ApiToken> findByTokenHash(String tokenHash) {
        return apiTokenRepository.findByTokenHash(tokenHash);
    }

    @CacheEvict(value = "apiTokens", key = "#token.tokenHash")
    public ApiToken saveToken(ApiToken token) {
        return apiTokenRepository.save(token);
    }
}
```

#### 7.1.5 OpenAI Service with Settings Integration

```java
@Service
@Slf4j
public class OpenAIClientService {

    private final WebClient webClient;
    private final SettingsService settingsService;
    private final CircuitBreaker circuitBreaker;
    private final Retry retry;
    private final String apiKey;

    public OpenAIClientService(WebClient.Builder webClientBuilder,
                             SettingsService settingsService) {
        this.settingsService = settingsService;
        this.apiKey = getOpenAiApiKey();

        this.webClient = webClientBuilder
            .baseUrl("https://api.openai.com/v1")
            .defaultHeaders(headers -> {
                headers.setBearerAuth(apiKey);
                headers.setContentType(MediaType.APPLICATION_JSON);
            })
            .clientConnector(new ReactorClientHttpConnector(
                HttpClient.create()
                    .compress(true)
                    .responseTimeout(Duration.ofSeconds(getTimeoutSeconds()))
                    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 30000)
            ))
            .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(16 * 1024 * 1024)) // 16MB
            .build();

        this.circuitBreaker = CircuitBreaker.ofDefaults("openai-api");
        this.retry = Retry.ofDefaults("openai-api");
    }

    public Mono<String> solveMathProblem(byte[] imageData, String prompt) {
        return webClient.post()
            .uri("/chat/completions")
            .bodyValue(buildRequest(imageData, prompt))
            .retrieve()
            .onStatus(HttpStatus::is4xxClientError, response ->
                Mono.error(new OpenAIClientException("Client error: " + response.statusCode())))
            .onStatus(HttpStatus::is5xxServerError, response ->
                Mono.error(new OpenAIClientException("Server error: " + response.statusCode())))
            .bodyToMono(OpenAIResponse.class)
            .map(this::extractAnswer)
            .transform(CircuitBreakerOperator.of(circuitBreaker))
            .transform(RetryOperator.of(retry))
            .timeout(Duration.ofSeconds(getTimeoutSeconds()))
            .onErrorMap(TimeoutException.class, ex ->
                new OpenAIClientException("Request timeout"))
            .onErrorMap(ExhaustedRetryException.class, ex ->
                new OpenAIClientException("Retry attempts exhausted"));
    }

    private String getModel() {
        return settingsService.getOpenAiModel();
    }

    private int getTimeoutSeconds() {
        return settingsService.getOpenAiTimeoutSeconds();
    }

    private String getOpenAiApiKey() {
        return StringUtils.hasText(apiKey) ? apiKey :
            System.getenv().getOrDefault("OPENAI_API_KEY", "");
    }

    private Object buildRequest(byte[] imageData, String prompt) {
        Map<String, Object> request = new HashMap<>();
        request.put("model", getModel());
        request.put("max_tokens", 300);

        List<Map<String, Object>> messages = new ArrayList<>();
        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");

        List<Map<String, Object>> content = new ArrayList<>();
        Map<String, Object> textContent = new HashMap<>();
        textContent.put("type", "text");
        textContent.put("text", prompt != null ? prompt : "Solve math problem in this image and provide only the numerical answer.");
        content.add(textContent);

        Map<String, Object> imageContent = new HashMap<>();
        imageContent.put("type", "image_url");
        Map<String, String> imageUrl = new HashMap<>();
        imageUrl.put("url", "data:image/jpeg;base64," + Base64.getEncoder().encodeToString(imageData));
        imageContent.put("image_url", imageUrl);
        content.add(imageContent);

        message.put("content", content);
        messages.add(message);
        request.put("messages", messages);

        return request;
    }

    public boolean healthCheck() {
        try {
            return webClient.get()
                .uri("/models")
                .retrieve()
                .bodyToMono(String.class)
                .map(response -> response.contains("gpt"))
                .timeout(Duration.ofSeconds(10))
                .block(Duration.ofSeconds(10));
        } catch (Exception e) {
            log.warn("OpenAI health check failed: {}", e.getMessage());
            return false;
        }
    }

    @EventListener
    public void handleSettingsUpdated(SettingsUpdatedEvent event) {
        log.info("Settings updated, OpenAI client will use new configuration");
        // Client will use new settings on next request due to SettingsService caching
    }
}
```

#### 7.1.3 Response Caching for Flow-Based Requests

```java
@Service
public class FlowCacheService {

    private final CacheManager cacheManager;
    private final MessageDigest messageDigest;

    public FlowCacheService(CacheManager cacheManager) {
        this.cacheManager = cacheManager;
        try {
            this.messageDigest = MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }

    public Optional<String> getCachedResponse(String flow, byte[] imageHash, String parameters) {
        String cacheKey = generateCacheKey(flow, imageHash, parameters);
        Cache cache = cacheManager.getCache("flowResponses");
        return Optional.ofNullable(cache.get(cacheKey, String.class));
    }

    public void cacheResponse(String flow, byte[] imageHash, String parameters, String response) {
        String cacheKey = generateCacheKey(flow, imageHash, parameters);
        Cache cache = cacheManager.getCache("flowResponses");
        cache.put(cacheKey, response);
    }

    private String generateCacheKey(String flow, byte[] imageHash, String parameters) {
        StringBuilder sb = new StringBuilder();
        sb.append(flow).append(":");
        sb.append(Base64.getEncoder().encodeToString(imageHash)).append(":");
        sb.append(parameters != null ? parameters : "");

        byte[] hash = messageDigest.digest(sb.toString().getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(hash);
    }
}
```

### 7.2 Database Performance Optimization

#### 7.2.1 Connection Pooling and Configuration

```yaml
spring:
  datasource:
    hikari:
      # Core connection settings
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000      # 5 minutes
      max-lifetime: 600000      # 10 minutes
      connection-timeout: 30000 # 30 seconds

      # Performance optimizations
      leak-detection-threshold: 60000  # 1 minute
      initialization-fail-timeout: 1
      validation-timeout: 5000
      connection-test-query: SELECT 1

      # Metrics
      register-mbeans: true
      metric-registry: application-metrics
```

#### 7.2.2 Query Optimization

```java
@Repository
public interface RequestLogRepository extends JpaRepository<RequestLog, UUID> {

    @Query(value = """
        SELECT rl FROM RequestLog rl
        WHERE rl.user.id = :userId
        AND rl.createdAt BETWEEN :startDate AND :endDate
        ORDER BY rl.createdAt DESC
        """,
        countQuery = """
        SELECT COUNT(rl) FROM RequestLog rl
        WHERE rl.user.id = :userId
        AND rl.createdAt BETWEEN :startDate AND :endDate
        """)
    Page<RequestLog> findByUserIdAndDateRange(
        @Param("userId") UUID userId,
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate,
        Pageable pageable);

    @Query(value = """
        SELECT new com.trc.platform.dto.UsageSummaryDto(
            COUNT(rl),
            COALESCE(SUM(rl.costCents), 0),
            AVG(rl.processingTimeMs)
        )
        FROM RequestLog rl
        WHERE rl.user.id = :userId
        AND rl.createdAt BETWEEN :startDate AND :endDate
        """)
    UsageSummaryDto getUsageSummary(
        @Param("userId") UUID userId,
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate);

    @Modifying
    @Query("UPDATE RequestLog rl SET rl.billingPeriod = :billingPeriod WHERE rl.id IN :requestIds")
    int updateBillingPeriodForRequests(
        @Param("billingPeriod") BillingPeriod billingPeriod,
        @Param("requestIds") List<UUID> requestIds);
}

#### 4.3.5 Settings Repository

```java
@Repository
public interface SettingsRepository extends JpaRepository<Settings, Long> {

    @Override
    @Query("SELECT s FROM Settings s WHERE s.id = 1")
    Optional<Settings> findById(Long id);

    @Override
    @Query("SELECT s FROM Settings s WHERE s.id = 1")
    Optional<Settings> findByExample(Example<Settings> example);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT s FROM Settings s WHERE s.id = 1")
    Settings findAndLockById();
}
```
```

#### 7.2.3 Batch Processing

```java
@Service
@Transactional
public class BatchProcessingService {

    @PersistenceContext
    private EntityManager entityManager;

    public void processBatchUpdates(List<RequestLog> requestLogs) {
        final int BATCH_SIZE = 50;

        for (int i = 0; i < requestLogs.size(); i++) {
            RequestLog log = requestLogs.get(i);
            entityManager.merge(log);

            if (i % BATCH_SIZE == 0 || i == requestLogs.size() - 1) {
                entityManager.flush();
                entityManager.clear();
            }
        }
    }

    public void batchInsertRequestLogs(List<RequestLog> requestLogs) {
        final int BATCH_SIZE = 50;

        for (int i = 0; i < requestLogs.size(); i++) {
            RequestLog log = requestLogs.get(i);
            entityManager.persist(log);

            if (i % BATCH_SIZE == 0 || i == requestLogs.size() - 1) {
                entityManager.flush();
                entityManager.clear();
            }
        }
    }
}
```

### 7.3 HTTP Client Performance

#### 7.3.1 WebClient Configuration for OpenAI API

```java
@Configuration
public class WebClientConfig {

    @Bean
    @Primary
    public WebClient webClient(WebClient.Builder builder) {
        return builder
            .baseUrl("https://api.openai.com/v1")
            .defaultHeaders(headers -> {
                headers.setBearerAuth("${OPENAI_API_KEY}");
                headers.setContentType(MediaType.APPLICATION_JSON);
            })
            .clientConnector(new ReactorClientHttpConnector(
                HttpClient.create()
                    .compress(true)
                    .responseTimeout(Duration.ofSeconds(60))
                    .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 30000)
            ))
            .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(16 * 1024 * 1024)) // 16MB
            .build();
    }
}
```

#### 7.3.2 OpenAI Client with Retry and Circuit Breaker

```java
@Service
public class OpenAIClientService {

    private final WebClient webClient;
    private final CircuitBreaker circuitBreaker;
    private final Retry retry;

    public OpenAIClientService(WebClient webClient) {
        this.webClient = webClient;
        this.circuitBreaker = CircuitBreaker.ofDefaults("openai-api");
        this.retry = Retry.ofDefaults("openai-api");
    }

    public Mono<String> solveMathProblem(byte[] imageData, String prompt) {
        return webClient.post()
            .uri("/chat/completions")
            .bodyValue(buildRequest(imageData, prompt))
            .retrieve()
            .onStatus(HttpStatus::is4xxClientError, response ->
                Mono.error(new OpenAIClientException("Client error: " + response.statusCode())))
            .onStatus(HttpStatus::is5xxServerError, response ->
                Mono.error(new OpenAIClientException("Server error: " + response.statusCode())))
            .bodyToMono(OpenAIResponse.class)
            .map(this::extractAnswer)
            .transform(CircuitBreakerOperator.of(circuitBreaker))
            .transform(RetryOperator.of(retry))
            .timeout(Duration.ofSeconds(30))
            .onErrorMap(TimeoutException.class, ex ->
                new OpenAIClientException("Request timeout"))
            .onErrorMap(ExhaustedRetryException.class, ex ->
                new OpenAIClientException("Retry attempts exhausted"));
    }

    private Object buildRequest(byte[] imageData, String prompt) {
        Map<String, Object> request = new HashMap<>();
        request.put("model", "gpt-4-vision-preview");
        request.put("max_tokens", 300);

        List<Map<String, Object>> messages = new ArrayList<>();
        Map<String, Object> message = new HashMap<>();
        message.put("role", "user");

        List<Map<String, Object>> content = new ArrayList<>();
        Map<String, Object> textContent = new HashMap<>();
        textContent.put("type", "text");
        textContent.put("text", prompt != null ? prompt : "Solve the math problem in this image and provide only the numerical answer.");
        content.add(textContent);

        Map<String, Object> imageContent = new HashMap<>();
        imageContent.put("type", "image_url");
        Map<String, String> imageUrl = new HashMap<>();
        imageUrl.put("url", "data:image/jpeg;base64," + Base64.getEncoder().encodeToString(imageData));
        imageContent.put("image_url", imageUrl);
        content.add(imageContent);

        message.put("content", content);
        messages.add(message);
        request.put("messages", messages);

        return request;
    }
}
```

---

## 9. Development Guidelines

### 9.1 Code Standards and Best Practices

#### 9.1.1 Code Style and Formatting

```xml
<!-- pom.xml - Checkstyle and SpotBless configuration -->
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-checkstyle-plugin</artifactId>
    <version>3.3.0</version>
    <configuration>
        <configLocation>checkstyle.xml</configLocation>
        <encoding>UTF-8</encoding>
        <consoleOutput>true</consoleOutput>
        <failsOnError>true</failsOnError>
    </configuration>
    <executions>
        <execution>
            <id>validate</id>
            <phase>validate</phase>
            <goals>
                <goal>check</goal>
            </goals>
        </execution>
    </executions>
</plugin>

<plugin>
    <groupId>com.diffplug.spotless</groupId>
    <artifactId>spotless-maven-plugin</artifactId>
    <version>2.41.1</version>
    <configuration>
        <java>
            <importOrder>
                <order>java,javax,org.springframework,com.trc.platform</order>
            </importOrder>
            <removeUnusedImports/>
            <googleJavaFormat/>
            <formatAnnotations/>
        </java>
    </configuration>
    <executions>
        <execution>
            <goals>
                <goal>check</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

#### 9.1.2 Exception Handling Strategy

```java
// Base exception class
@Data
@EqualsAndHashCode(callSuper = true)
public class TrcPlatformException extends RuntimeException {
    private final String errorCode;
    private final HttpStatus httpStatus;

    public TrcPlatformException(String message, String errorCode, HttpStatus httpStatus) {
        super(message);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }

    public TrcPlatformException(String message, String errorCode, HttpStatus httpStatus, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
        this.httpStatus = httpStatus;
    }
}

// Specific exceptions
public class UserNotFoundException extends TrcPlatformException {
    public UserNotFoundException(String message) {
        super(message, "USER_NOT_FOUND", HttpStatus.NOT_FOUND);
    }
}

public class ValidationException extends TrcPlatformException {
    public ValidationException(String message) {
        super(message, "VALIDATION_ERROR", HttpStatus.BAD_REQUEST);
    }
}

public class OpenAIClientException extends TrcPlatformException {
    public OpenAIClientException(String message) {
        super(message, "OPENAI_CLIENT_ERROR", HttpStatus.SERVICE_UNAVAILABLE);
    }
}

// Global exception handler
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(TrcPlatformException.class)
    public ResponseEntity<ApiResponse<Void>> handleTrcPlatformException(TrcPlatformException ex) {
        ApiResponse<Void> response = ApiResponse.error(ex.getMessage(), ex.getErrorCode());
        return ResponseEntity.status(ex.getHttpStatus()).body(response);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidationException(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult().getFieldErrors().stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.joining(", "));
        ApiResponse<Void> response = ApiResponse.error(message, "VALIDATION_ERROR");
        return ResponseEntity.badRequest().body(response);
    }

    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ApiResponse<Void>> handleAccessDeniedException(AccessDeniedException ex) {
        ApiResponse<Void> response = ApiResponse.error("Access denied", "ACCESS_DENIED");
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(Exception ex) {
        log.error("Unexpected error occurred", ex);
        ApiResponse<Void> response = ApiResponse.error("Internal server error", "INTERNAL_ERROR");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }
}
```

#### 9.1.3 Logging Strategy

```xml
<!-- logback-spring.xml -->
<configuration>
    <springProfile name="!prod">
        <include resource="org/springframework/boot/logging/logback/defaults.xml"/>
        <property name="LOG_FILE" value="${LOG_FILE:-${LOG_PATH:-${LOG_TEMP:-${java.io.tmpdir:-/tmp}}/}spring.log"/>
        <include resource="org/springframework/boot/logging/logback/console-appender.xml"/>
        <root level="INFO">
            <appender-ref ref="CONSOLE"/>
        </root>
    </springProfile>

    <springProfile name="prod">
        <appender name="JSON_CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
            <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
                <providers>
                    <timestamp/>
                    <logLevel/>
                    <loggerName/>
                    <mdc/>
                    <message/>
                    <stackTrace/>
                </providers>
            </encoder>
        </appender>

        <root level="INFO">
            <appender-ref ref="JSON_CONSOLE"/>
        </root>
    </springProfile>

    <logger name="com.trc.platform" level="DEBUG"/>
    <logger name="org.springframework.security" level="DEBUG"/>
    <logger name="org.springframework.web" level="DEBUG"/>
</configuration>
```

### 9.2 Development Environment Setup

*Note: For Docker-based development setup, see [JAVA_TECHNICAL_SPECIFICATION_K8S.md](JAVA_TECHNICAL_SPECIFICATION_K8S.md#development-environment-setup)*

### 9.3 Code Quality Tools

#### 9.3.1 SonarQube Configuration

```xml
<!-- pom.xml -->
<plugin>
    <groupId>org.sonarsource.scanner.maven</groupId>
    <artifactId>sonar-maven-plugin</artifactId>
    <version>3.10.0.2594</version>
</plugin>
```

```yaml
# .github/workflows/sonar.yml
name: SonarQube Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up JDK 21
      uses: actions/setup-java@v4
      with:
        java-version: '21'
        distribution: 'temurin'

    - name: Cache SonarQube packages
      uses: actions/cache@v3
      with:
        path: ~/.sonar/cache
        key: ${{ runner.os }}-sonar
        restore-keys: ${{ runner.os }}-sonar

    - name: Cache Maven dependencies
      uses: actions/cache@v3
      with:
        path: ~/.m2
        key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
        restore-keys: ${{ runner.os }}-m2

    - name: Build and analyze
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      run: ./mvnw verify sonar:sonar -Dsonar.projectKey=trc-platform-backend
```

---

## 10. Testing Strategy

### 10.1 Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │
                    │    (5%)         │
                    └─────────────────┘
                ┌─────────────────────────┐
                │   Integration Tests     │
                │       (25%)           │
                └─────────────────────────┘
        ┌─────────────────────────────────────────┐
        │           Unit Tests                      │
        │               (70%)                      │
        └─────────────────────────────────────────┘
```

### 10.2 Unit Testing

#### 10.2.1 Service Layer Testing

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;

    @Test
    @DisplayName("Should create user successfully")
    void shouldCreateUserSuccessfully() {
        // Given
        RegistrationRequest request = RegistrationRequest.builder()
            .email("test@example.com")
            .password("SecurePassword123!")
            .acceptedTerms(true)
            .acknowledgedDisclaimer(true)
            .build();

        User savedUser = User.builder()
            .id(UUID.randomUUID())
            .email("test@example.com")
            .passwordHash("encoded_password")
            .active(true)
            .dateJoined(LocalDateTime.now())
            .build();

        when(userRepository.existsByEmail("test@example.com")).thenReturn(false);
        when(passwordEncoder.encode("SecurePassword123!")).thenReturn("encoded_password");
        when(userRepository.save(any(User.class))).thenReturn(savedUser);

        // When
        UserDto result = userService.createUser(request);

        // Then
        assertThat(result.getEmail()).isEqualTo("test@example.com");
        verify(passwordEncoder).encode("SecurePassword123!");
        verify(userRepository).save(any(User.class));
        verify(emailService).sendVerificationEmail(any(User.class));
    }

    @Test
    @DisplayName("Should throw exception when email already exists")
    void shouldThrowExceptionWhenEmailAlreadyExists() {
        // Given
        RegistrationRequest request = RegistrationRequest.builder()
            .email("existing@example.com")
            .password("SecurePassword123!")
            .acceptedTerms(true)
            .acknowledgedDisclaimer(true)
            .build();

        when(userRepository.existsByEmail("existing@example.com")).thenReturn(true);

        // When & Then
        assertThatThrownBy(() -> userService.createUser(request))
            .isInstanceOf(UserAlreadyExistsException.class)
            .hasMessage("User already exists with email: existing@example.com");

        verify(userRepository, never()).save(any(User.class));
        verify(emailService, never()).sendVerificationEmail(any(User.class));
    }
}
```

#### 10.2.2 Controller Layer Testing

```java
@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @WithMockUser(roles = {"USER"})
    @DisplayName("Should get current user successfully")
    void shouldGetCurrentUserSuccessfully() throws Exception {
        // Given
        UserDto userDto = UserDto.builder()
            .id(UUID.randomUUID())
            .email("test@example.com")
            .emailVerified(true)
            .dateJoined(LocalDateTime.now())
            .build();

        when(userService.getCurrentUser()).thenReturn(userDto);

        // When & Then
        mockMvc.perform(get("/api/v1/users/me")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.email").value("test@example.com"))
                .andExpect(jsonPath("$.data.emailVerified").value(true));
    }

    @Test
    @DisplayName("Should return 401 when not authenticated")
    void shouldReturn401WhenNotAuthenticated() throws Exception {
        mockMvc.perform(get("/api/v1/users/me")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isUnauthorized());
    }
}
```

### 10.3 Integration Testing

#### 10.3.1 Repository Integration Testing

```java
@DataJpaTest
@Testcontainers
class RequestLogRepositoryIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("test_db")
            .withUsername("test")
            .withPassword("test");

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private RequestLogRepository requestLogRepository;

    @Test
    @DisplayName("Should find requests by user and date range")
    void shouldFindRequestsByUserAndDateRange() {
        // Given
        User user = User.builder()
            .email("test@example.com")
            .passwordHash("hash")
            .build();
        entityManager.persist(user);

        RequestLog request1 = RequestLog.builder()
            .user(user)
            .createdAt(LocalDateTime.now().minusDays(2))
            .build();
        entityManager.persist(request1);

        RequestLog request2 = RequestLog.builder()
            .user(user)
            .createdAt(LocalDateTime.now().minusDays(1))
            .build();
        entityManager.persist(request2);

        RequestLog request3 = RequestLog.builder()
            .user(user)
            .createdAt(LocalDateTime.now().minusDays(5))
            .build();
        entityManager.persist(request3);

        // When
        LocalDateTime startDate = LocalDateTime.now().minusDays(3);
        LocalDateTime endDate = LocalDateTime.now();
        Page<RequestLog> result = requestLogRepository.findByUserIdAndDateRange(
            user.getId(), startDate, endDate, Pageable.ofSize(10));

        // Then
        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getContent()).extracting("id")
            .containsExactlyInAnyOrder(request1.getId(), request2.getId());
    }
}
```

#### 10.3.2 API Integration Testing

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class UserIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("integration_test_db")
            .withUsername("test")
            .withPassword("test");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
            .withExposedPorts(6379);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.redis.host", redis::getHost);
        registry.add("spring.redis.port", redis::getFirstMappedPort);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    @DisplayName("Should complete user registration flow")
    void shouldCompleteUserRegistrationFlow() {
        // Registration
        RegistrationRequest registrationRequest = RegistrationRequest.builder()
            .email("integration@example.com")
            .password("SecurePassword123!")
            .acceptedTerms(true)
            .acknowledgedDisclaimer(true)
            .build();

        ResponseEntity<ApiResponse> registrationResponse = restTemplate.postForEntity(
            "/api/v1/auth/register", registrationRequest, ApiResponse.class);

        assertThat(registrationResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(registrationResponse.getBody().isSuccess()).isTrue();

        // Login
        LoginRequest loginRequest = LoginRequest.builder()
            .email("integration@example.com")
            .password("SecurePassword123!")
            .build();

        ResponseEntity<ApiResponse> loginResponse = restTemplate.postForEntity(
            "/api/v1/auth/login", loginRequest, ApiResponse.class);

        assertThat(loginResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(loginResponse.getBody().isSuccess()).isTrue();

        // Get current user with session token
        String sessionToken = (String) ((Map<String, Object>) loginResponse.getBody().getData()).get("sessionToken");
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(sessionToken);
        HttpEntity<String> entity = new HttpEntity<>(headers);

        ResponseEntity<ApiResponse> userResponse = restTemplate.exchange(
            "/api/v1/users/me", HttpMethod.GET, entity, ApiResponse.class);

        assertThat(userResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(userResponse.getBody().isSuccess()).isTrue();

        Map<String, Object> userData = (Map<String, Object>) userResponse.getBody().getData();
        assertThat(userData.get("email")).isEqualTo("integration@example.com");
    }
}
```

### 10.4 Performance Testing

#### 10.4.1 Load Testing with JMeter

```xml
<!-- jmeter/load-test.jmx -->
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="TRC Platform Load Test" enabled="true">
      <stringProp name="TestPlan.comments">Load test for TRC Platform API</stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="BASE_URL" elementType="Argument">
            <stringProp name="Argument.name">BASE_URL</stringProp>
            <stringProp name="Argument.value">http://localhost:8080</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="API Users" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">10</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">50</stringProp>
        <stringProp name="ThreadGroup.ramp_time">5</stringProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.duration"></stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Health Check" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">${BASE_URL}</stringProp>
          <stringProp name="HTTPSampler.port">8080</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">/api/v1/core/health</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### 10.5 Test Configuration

#### 10.5.1 Test Application Properties

```yaml
# application-test.yml
spring:
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
    username: sa
    password:

  jpa:
    hibernate:
      ddl-auto: create-drop
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.H2Dialect

  redis:
    host: localhost
    port: 6379

  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: http://localhost:8080

logging:
  level:
    com.trc.platform: DEBUG
    org.springframework.security: DEBUG
    org.springframework.web: DEBUG
```

---

## 11. Database Migration Strategy

### 11.1 Flyway Migration Approach

#### 11.1.1 Migration Philosophy

The Java backend will use **Flyway** for database schema management, providing:
- **Versioned Migrations**: Each migration has a unique version number
- **Idempotent Operations**: Migrations can be safely re-run
- **Rollback Support**: Ability to undo problematic migrations
- **Environment Consistency**: Same schema across all environments

#### 11.1.2 Migration Directory Structure

```
src/main/resources/db/migration/
├── V1__Create_user_tables.sql
├── V2__Create_core_tables.sql
├── V3__Create_usage_tables.sql
├── V4__Add_settings_table.sql
├── V5__Add_indexes.sql
├── V6__Create_default_settings.sql
└── V7__Add_constraints.sql
```

#### 11.1.3 Initial Migration Scripts

```sql
-- V1__Create_user_tables.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_staff BOOLEAN NOT NULL DEFAULT false,
    email_verified_at TIMESTAMP,
    date_joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_accepted_terms BOOLEAN NOT NULL DEFAULT false,
    user_acknowledged_disclaimer BOOLEAN NOT NULL DEFAULT false,
    version BIGINT NOT NULL DEFAULT 0
);

-- V2__Create_core_tables.sql
CREATE TABLE api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    token_prefix VARCHAR(12) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT true,
    usage_count BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE settings (
    id BIGINT PRIMARY KEY DEFAULT 1,
    cost_per_request_cents INTEGER NOT NULL DEFAULT 100,
    openai_model VARCHAR(100) DEFAULT 'gpt-4-vision-preview',
    openai_timeout_s INTEGER NOT NULL DEFAULT 30,
    app_domain VARCHAR(255),
    save_request_images BOOLEAN NOT NULL DEFAULT false,
    max_saved_image_size_mb INTEGER NOT NULL DEFAULT 10,
    image_retention_days INTEGER NOT NULL DEFAULT 30,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT settings_single_record CHECK (id = 1)
);

-- V3__Create_usage_tables.sql
CREATE TABLE billing_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_requests INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    is_current BOOLEAN NOT NULL DEFAULT false,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    version BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    billing_period_id UUID REFERENCES billing_periods(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms BIGINT NOT NULL,
    status_code INTEGER NOT NULL,
    error_message TEXT,
    cost_cents INTEGER NOT NULL,
    api_endpoint VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address INET
);


-- V6__Create_default_settings.sql
INSERT INTO settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
```

#### 11.1.4 Flyway Configuration

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    baseline-version: 0
    validate-on-migrate: true
    clean-disabled: true
    out-of-order: false
    sql-migration-prefix: V
    sql-migration-separator: __
    repeatable-sql-migration-prefix: R
    target: latest
```

#### 11.1.5 Production Deployment Strategy

*Note: For detailed Kubernetes production deployment strategies, see [JAVA_TECHNICAL_SPECIFICATION_K8S.md](JAVA_TECHNICAL_SPECIFICATION_K8S.md#production-deployment-strategy)*

**Schema First Approach:**
1. **Deploy New Java Application**: Point to separate database schema
2. **Run Flyway Migrations**: Create all tables and indexes
3. **Data Validation**: Verify schema matches Django structure
4. **Data Sync**: One-time sync of user data if needed
5. **DNS Switch**: Point traffic to Java application
6. **Monitor**: Ensure everything works as expected
7. **Retire Django**: Decommission old Django application

### 11.2 Database Connection and Pooling

#### 11.2.1 Production Database Configuration

```yaml
# application-prod.yml
spring:
  datasource:
    url: ${DATABASE_URL}
    username: ${DATABASE_USERNAME}
    password: ${DATABASE_PASSWORD}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000
      max-lifetime: 600000
      connection-timeout: 30000
      leak-detection-threshold: 60000
      pool-name: "trc-platform-hikari-pool"

  jpa:
    hibernate:
      ddl-auto: validate  # Use Flyway for schema management
    show-sql: false
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: false
        jdbc:
          batch_size: 50
          fetch_size: 50
        connection:
          provider_disables_autocommit: true
        order_inserts: true
        order_updates: true
        batch_versioned_data: true
        generate_statistics: false
        session:
          events:
            log:
              level: false
```

#### 11.2.2 Flyway Migration Service

```java
@Component
@Slf4j
public class DatabaseMigrationService {

    @Autowired
    private Flyway flyway;

    @EventListener(ApplicationReadyEvent.class)
    public void onApplicationReady() {
        try {
            migrateDatabase();
        } catch (Exception e) {
            log.error("Database migration failed", e);
            System.exit(1); // Fail fast if migration fails
        }
    }

    public void migrateDatabase() {
        log.info("Starting database migration...");

        FlywayMigrationResult result = flyway.migrateWithResult();

        if (result.successfulMigrations.isEmpty() && result.pendingMigrations.isEmpty()) {
            log.info("Database is up to date");
            return;
        }

        log.info("Migration completed. Success: {}, Pending: {}, Failed: {}",
            result.successfulMigrations.size(),
            result.pendingMigrations.size(),
            result.failedMigrations.size());

        if (!result.failedMigrations.isEmpty()) {
            result.failedMigrations.forEach(failed ->
                log.error("Migration {} failed: {}", failed.getVersion(), failed.getError()));
            throw new MigrationException("Database migration failed");
        }

        result.successfulMigrations.forEach(migration ->
            log.info("Migration {} applied successfully", migration.getVersion()));
    }

    public MigrationInfoService getMigrationInfo() {
        return flyway.info();
    }

    public void validateDatabase() {
        try {
            FlywayMigrationResult result = flyway.validateWithResult();
            if (result.validationFailed) {
                log.error("Database validation failed");
                throw new MigrationException("Database validation failed");
            }
            log.info("Database validation completed successfully");
        } catch (FlywayValidationException e) {
            log.error("Database validation failed", e);
            throw new MigrationException("Database validation failed", e);
        }
    }
}
```

### 11.3 Cut-over Strategy

*Note: For detailed blue-green deployment and production cut-over procedures, see [JAVA_TECHNICAL_SPECIFICATION_K8S.md](JAVA_TECHNICAL_SPECIFICATION_K8S.md#blue-green-deployment)*

**Step 1: Schema Validation**
```bash
# Validate Flyway migrations before deployment
./mvnw flyway:validate -Dflyway.url=$DATABASE_URL -Dflyway.user=$DATABASE_USER -Dflyway.password=$DATABASE_PASSWORD
```

---

## 12. Monitoring & Observability

### 12.1 Application Metrics

#### 12.1.1 Micrometer Configuration

```java
@Configuration
public class MetricsConfig {

    @Bean
    public MeterRegistryCustomizer<MeterRegistry> metricsCommonTags() {
        return registry -> registry.config().commonTags(
            "application", "trc-platform-backend",
            "version", getClass().getPackage().getImplementationVersion()
        );
    }

    @Bean
    public TimedAspect timedAspect(MeterRegistry registry) {
        return new TimedAspect(registry);
    }

    @Bean
    public CountedAspect countedAspect(MeterRegistry registry) {
        return new CountedAspect(registry);
    }
}

@Service
public class MetricsService {

    private final Counter imageProcessingCounter;
    private final Timer imageProcessingTimer;
    private final Gauge activeUsersGauge;

    public MetricsService(MeterRegistry meterRegistry) {
        this.imageProcessingCounter = Counter.builder("api.requests")
            .description("Total API requests")
            .tag("endpoint", "solve")
            .register(meterRegistry);

        this.imageProcessingTimer = Timer.builder("image.processing.time")
            .description("Image processing time")
            .register(meterRegistry);

        this.activeUsersGauge = Gauge.builder("users.active")
            .description("Number of active users")
            .register(meterRegistry, this, MetricsService::getActiveUserCount);
    }

    public void recordImageProcessingStart() {
        imageProcessingCounter.increment(Tags.of("status", "started"));
    }

    public void recordImageProcessingSuccess(Timer.Sample sample) {
        sample.stop(imageProcessingTimer);
        imageProcessingCounter.increment(Tags.of("status", "success"));
    }

    public void recordImageProcessingError(Exception error) {
        imageProcessingCounter.increment(
            Tags.of("status", "error", "error_type", error.getClass().getSimpleName()));
    }

    private double getActiveUserCount() {
        // Implementation to get active user count
        return activeUserService.getActiveUserCount();
    }
}
```

#### 12.1.2 Custom Metrics

```java
@RestController
@RequestMapping("/api/v1/core")
public class CoreController {

    private final MetricsService metricsService;

    @PostMapping("/solve")
    @Timed(name = "api.solve.duration", description = "Duration of solve API calls")
    @Counted(name = "api.solve.count", description = "Number of solve API calls")
    public ResponseEntity<ApiResponse<SolveResponseDto>> solve(
            @Valid @ModelAttribute SolveRequest request) {

        Timer.Sample sample = Timer.start();
        metricsService.recordImageProcessingStart();

        try {
            SolveResponseDto response = imageProcessingService.solve(request);
            metricsService.recordImageProcessingSuccess(sample);
            return ResponseEntity.ok(ApiResponse.success(response));

        } catch (Exception e) {
            metricsService.recordImageProcessingError(e);
            throw e;
        }
    }
}
```

### 12.2 Health Checks

#### 12.2.1 Custom Health Indicators

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {

    @Autowired
    private DataSource dataSource;

    @Override
    public Health health() {
        try {
            Connection connection = dataSource.getConnection();
            boolean isValid = connection.isValid(1);
            connection.close();

            if (isValid) {
                return Health.up()
                    .withDetail("database", "Available")
                    .withDetail("validation", "Successful")
                    .build();
            } else {
                return Health.down()
                    .withDetail("database", "Connection invalid")
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("database", "Connection failed")
                .withException(e)
                .build();
        }
    }
}

@Component
public class RedisHealthIndicator implements HealthIndicator {

    @Autowired
    private RedisConnectionFactory redisConnectionFactory;

    @Override
    public Health health() {
        try {
            RedisConnectionFactory factory = redisConnectionFactory;
            RedisConnection connection = factory.getConnection();
            connection.ping();
            connection.close();

            return Health.up()
                .withDetail("redis", "Available")
                .build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("redis", "Connection failed")
                .withException(e)
                .build();
        }
    }
}

@Component
public class OpenAIHealthIndicator implements HealthIndicator {

    @Autowired
    private OpenAIClientService openAIClientService;

    @Override
    public Health health() {
        try {
            // Perform a simple health check on OpenAI API
            boolean isHealthy = openAIClientService.healthCheck();

            if (isHealthy) {
                return Health.up()
                    .withDetail("openai", "Available")
                    .build();
            } else {
                return Health.down()
                    .withDetail("openai", "Service unavailable")
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("openai", "Health check failed")
                .withException(e)
                .build();
        }
    }
}
```

#### 12.2.2 Liveness and Readiness Probes

```java
@Component
public class ApplicationStateTracker {

    private volatile boolean isReady = false;
    private volatile boolean isAlive = true;
    private final AtomicLong lastActivityTime = new AtomicLong(System.currentTimeMillis());

    @EventListener
    public void handleApplicationReady(ApplicationReadyEvent event) {
        isReady = true;
    }

    @EventListener
    public void handleContextClosed(ContextClosedEvent event) {
        isAlive = false;
        isReady = false;
    }

    public void recordActivity() {
        lastActivityTime.set(System.currentTimeMillis());
    }

    public boolean isReady() {
        return isReady;
    }

    public boolean isAlive() {
        return isAlive && (System.currentTimeMillis() - lastActivityTime.get() < 60000);
    }
}

@Component
public class LivenessHealthIndicator implements HealthIndicator {

    @Autowired
    private ApplicationStateTracker stateTracker;

    @Override
    public Health health() {
        if (stateTracker.isAlive()) {
            return Health.up()
                .withDetail("status", "Application is alive")
                .build();
        } else {
            return Health.down()
                .withDetail("status", "Application is not alive")
                .build();
        }
    }
}

@Component
public class ReadinessHealthIndicator implements HealthIndicator {

    @Autowired
    private ApplicationStateTracker stateTracker;

    @Override
    public Health health() {
        if (stateTracker.isReady()) {
            return Health.up()
                .withDetail("status", "Application is ready")
                .build();
        } else {
            return Health.down()
                .withDetail("status", "Application is not ready")
                .build();
        }
    }
}
```

### 12.3 Distributed Tracing

#### 12.3.1 OpenTelemetry Configuration

```java
@Configuration
public class TracingConfig {

    @Bean
    public OpenTelemetry openTelemetry() {
        return OpenTelemetrySdk.builder()
            .setTracerProvider(
                SdkTracerProvider.builder()
                    .addSpanProcessor(BatchSpanProcessor.builder(
                        JaegerGrpcSpanExporter.builder()
                            .setEndpoint("http://jaeger:14250")
                            .build())
                        .build())
                    .setResource(Resource.getDefault()
                        .merge(Resource.builder()
                            .put(ResourceAttributes.SERVICE_NAME, "trc-platform-backend")
                            .put(ResourceAttributes.SERVICE_VERSION, "1.0.0")
                            .build()))
                    .build())
            .setMeterProvider(
                SdkMeterProvider.builder()
                    .registerMetricReader(
                        PeriodicMetricReader.builder(
                            PrometheusHttpServer.builder()
                                .setPort(9090)
                                .build())
                        .setInterval(Duration.ofSeconds(30))
                        .build())
                    .build())
            .build();
    }
}

@RestController
@RequestMapping("/api/v1/core")
public class CoreController {

    private final Tracer tracer;

    public CoreController(OpenTelemetry openTelemetry) {
        this.tracer = openTelemetry.getTracer(CoreController.class.getName());
    }

    @PostMapping("/solve")
    public ResponseEntity<ApiResponse<SolveResponseDto>> solve(
            @Valid @ModelAttribute SolveRequest request) {

        Span span = tracer.spanBuilder("solve-math-problem")
            .setAttribute("user.id", request.getUserId().toString())
            .setAttribute("image.size", request.getImage().getSize())
            .startSpan();

        try (Scope scope = span.makeCurrent()) {
            // Process image
            SolveResponseDto response = imageProcessingService.solve(request);

            span.setAttribute("processing.success", true);
            span.setAttribute("result.confidence", response.getConfidence());

            return ResponseEntity.ok(ApiResponse.success(response));

        } catch (Exception e) {
            span.recordException(e);
            span.setAttribute("processing.success", false);
            throw e;
        } finally {
            span.end();
        }
    }
}
```

### 12.4 Logging and Structured Logging

#### 12.4.1 Structured Logging Configuration

```java
@Component
public class StructuredLogger {

    private static final Logger structuredLogger = LoggerFactory.getLogger("STRUCTURED");

    public void logApiRequest(String userId, String endpoint, String method, String requestId) {
        MDC.put("userId", userId);
        MDC.put("endpoint", endpoint);
        MDC.put("method", method);
        MDC.put("requestId", requestId);

        structuredLogger.info("API request received");

        MDC.clear();
    }

    public void logImageProcessing(String userId, String requestId, long processingTime, boolean success) {
        MDC.put("userId", userId);
        MDC.put("requestId", requestId);
        MDC.put("processingTime", String.valueOf(processingTime));
        MDC.put("success", String.valueOf(success));
        MDC.put("event", "image_processing");

        if (success) {
            structuredLogger.info("Image processing completed successfully");
        } else {
            structuredLogger.error("Image processing failed");
        }

        MDC.clear();
    }

    public void logError(String userId, String requestId, String errorType, String errorMessage) {
        MDC.put("userId", userId);
        MDC.put("requestId", requestId);
        MDC.put("errorType", errorType);
        MDC.put("event", "error");

        structuredLogger.error("Error occurred: {}", errorMessage);

        MDC.clear();
    }
}
```

#### 12.4.2 Request/Response Logging Filter

```java
@Component
public class LoggingFilter extends OncePerRequestFilter {

    private final StructuredLogger structuredLogger;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                  HttpServletResponse response,
                                  FilterChain filterChain) throws ServletException, IOException {

        String requestId = UUID.randomUUID().toString();
        String userId = extractUserId(request);

        long startTime = System.currentTimeMillis();

        // Log request
        structuredLogger.logApiRequest(
            userId,
            request.getRequestURI(),
            request.getMethod(),
            requestId
        );

        try {
            filterChain.doFilter(request, response);

            long processingTime = System.currentTimeMillis() - startTime;

            // Log response
            MDC.put("requestId", requestId);
            MDC.put("processingTime", String.valueOf(processingTime));
            MDC.put("statusCode", String.valueOf(response.getStatus()));
            MDC.put("event", "api_response");

            structuredLogger.info("API request completed");
            MDC.clear();

        } catch (Exception e) {
            long processingTime = System.currentTimeMillis() - startTime;

            structuredLogger.logError(
                userId,
                requestId,
                e.getClass().getSimpleName(),
                e.getMessage()
            );

            throw e;
        }
    }

    private String extractUserId(HttpServletRequest request) {
        // Extract user ID from JWT token or API token
        String authorization = request.getHeader("Authorization");
        if (authorization != null && authorization.startsWith("Bearer ")) {
            try {
                String token = authorization.substring(7);
                if (token.startsWith("tok_")) {
                    // API token
                    return extractUserIdFromApiToken(token);
                } else {
                    // JWT token
                    return extractUserIdFromJwt(token);
                }
            } catch (Exception e) {
                // Log and continue
                log.warn("Failed to extract user ID from token: {}", e.getMessage());
            }
        }
        return "anonymous";
    }
}
```

### 12.5 Alerting and Notification

#### 12.5.1 Alert Configuration

```yaml
# prometheus/alerts.yml
groups:
- name: trc-platform-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second for the last 5 minutes"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m])) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency detected"
      description: "95th percentile latency is {{ $value }} seconds"

  - alert: ImageProcessingFailures
    expr: rate(image_processing_total{status="error"}[5m]) > 0.05
    for: 3m
    labels:
      severity: critical
    annotations:
      summary: "Image processing failures detected"
      description: "Image processing error rate is {{ $value }} failures per second"

  - alert: DatabaseConnectionFailure
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database connection failure"
      description: "Cannot connect to PostgreSQL database"

  - alert: RedisConnectionFailure
    expr: up{job="redis"} == 0
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Redis connection failure"
      description: "Cannot connect to Redis cache"
```

#### 12.5.2 Alert Service

```java
@Service
public class AlertService {

    @Autowired
    private NotificationService notificationService;

    @EventListener
    public void handleHighErrorRate(MetricAlertEvent event) {
        if ("HighErrorRate".equals(event.getAlertName())) {
            String message = String.format(
                "High error rate detected: %.2f errors/sec for the last %d minutes",
                event.getValue(),
                event.getDurationMinutes()
            );

            notificationService.sendAlert(
                AlertLevel.CRITICAL,
                "High Error Rate",
                message
            );
        }
    }

    @EventListener
    public void handleImageProcessingFailure(ImageProcessingFailureEvent event) {
        String message = String.format(
            "Image processing failed for user %s: %s",
            event.getUserId(),
            event.getErrorMessage()
        );

        notificationService.sendAlert(
            AlertLevel.WARNING,
            "Image Processing Failure",
            message
        );
    }
}
```

---

## Conclusion

This comprehensive technical specification provides a detailed roadmap for rewriting the TRC Platform backend from Django to Java using Spring Boot 3. The specification covers all aspects of the modern enterprise Java development lifecycle, including:

- **Technology Stack Selection**: Spring Boot 3 with Java 21 for enterprise readiness
- **Architecture Design**: Modular design with clear separation of concerns
- **Security**: Multi-modal authentication with JWT and API tokens
- **Performance**: Multi-level caching and optimized database access
- **Deployment**: Container-first approach with Kubernetes support
- **Observability**: Comprehensive monitoring, tracing, and alerting
- **Migration**: Phased approach with data validation

The implementation will provide improved performance, enhanced security, better maintainability, and cloud-native deployment capabilities while maintaining full API compatibility with the existing Django implementation.

**Next Steps**:
1. Set up development environment and CI/CD pipeline
2. Implement Flyway database migration scripts
3. Begin Phase 1 implementation with core project structure
4. Implement user management and authentication systems
5. Progress through remaining phases following development plan
6. Conduct thorough testing before production deployment

This specification serves as the foundation for building a robust, scalable, and maintainable Java backend that will support the TRC Platform's growth and evolution.
