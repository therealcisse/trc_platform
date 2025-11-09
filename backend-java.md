# TRC Platform Backend-Java Deep Analysis

Based on my comprehensive study of the backend-java product, here's a detailed analysis of the system:

## **Architecture Overview**

The TRC Platform is a **modern Spring Boot 3.5.7 application** built with **Java 21** that provides mathematical problem-solving services via OpenAI integration. It follows **domain-driven design** with clear bounded contexts and enterprise-grade quality standards.

### **Core Business Domains**

1. **Users Domain** (`com.trc.platform.users`)
   - User authentication, registration, API token management
   - Multi-factor authentication (email verification + invite codes)
   - JWT and API token-based authentication

2. **Core Domain** (`com.trc.platform.core`)
   - Mathematical problem solving using OpenAI API
   - Image processing for math problems
   - Reactive HTTP client integration

3. **Usage Domain** (`com.trc.platform.usage`)
   - Request logging and billing calculation
   - Period-based billing aggregation
   - Usage analytics and reporting

4. **Admin Domain** (`com.trc.platform.admin`)
   - Invite code management
   - Billing period administration
   - System configuration

## **Database Architecture**

### **Schema Design Principles**
- **UUID Primary Keys**: All entities use UUID for distributed system compatibility
- **Optimistic Locking**: `@Version` columns prevent concurrent modification conflicts
- **Soft Deletion**: Logical deletion patterns preserve data integrity
- **Period-Based Billing**: Costs aggregated monthly, not per-request

### **Core Tables**
1. **users** - Central user accounts with authentication and profile management
2. **api_tokens** - Programmatic access tokens with lifecycle management
3. **billing_periods** - Monthly billing cycles with aggregated cost tracking
4. **request_logs** - Comprehensive API request logging for usage tracking
5. **invite_codes** - User invitation system with expiration management
6. **settings** - System-wide configuration parameters

### **Key Relationships**
```
users (1) ───→ (N) api_tokens ───→ (N) request_logs
   │              │
   │              └──→ (N) request_logs
   │
   ├──→ (N) billing_periods ───→ (N) request_logs
   │
   ├──→ (N) invite_codes (created_by/used_by)
```

## **Security Architecture**

### **Multi-Layered Authentication**
- **JWT Tokens**: For web sessions with configurable TTL (default 24 hours)
- **API Tokens**: For programmatic access with secure hashing
- **Role-Based Access**: Admin endpoints protected with `@PreAuthorize("hasRole('ADMIN')")`
- **Stateless Design**: No server-side sessions, all token-based

### **Security Measures**
- **Password Hashing**: Argon2 algorithm for secure storage
- **Token Security**: Secure hashing, not storing actual tokens
- **Multi-Factor Auth**: Email verification + invite code requirement
- **Input Validation**: Comprehensive validation using Spring Validation

## **API Design**

### **RESTful Endpoints**
- **Core**: `/api/core/solve` - Math problem solving from images
- **Users**: `/api/customers/login`, `/api/customers/register` - Authentication
- **Billing**: `/api/billing/current` - Current billing information
- **Usage**: `/api/usage/summary` - Usage analytics
- **Admin**: `/api/v1/admin/*` - Administrative functions

### **Documentation Structure**
Comprehensive API documentation organized by domain in `api-docs/`:
- **admin/** - Administrative endpoints
- **billing/** - Billing and payment endpoints
- **core/** - Math solving endpoints
- **usage/** - Usage analytics endpoints
- **users/** - User management endpoints

## **External Integrations**

### **OpenAI Integration**
- **Core Processing Service**: Mathematical problem solving via GPT-4
- **Reactive WebClient**: Non-blocking HTTP calls
- **Error Handling**: Comprehensive retry and fallback mechanisms
- **Cost Tracking**: Real-time cost calculation per request

### **Email Service**
- **Verification System**: Email verification for account activation
- **SMTP Integration**: Configurable email provider
- **Template Support**: Professional email templates

## **Quality Standards**

### **Code Quality Tools**
- **Spotless**: Google Java Format with automatic import cleanup
- **JaCoCo**: Minimum 70% code coverage requirement
- **PMD**: Custom ruleset for static analysis
- **SpotBugs**: Maximum effort, low report level bug detection
- **Checkstyle**: 120-character line limit enforcement
- **ErrorProne**: Compile-time error detection
- **OWASP Dependency Check**: Security vulnerability scanning

### **Testing Strategy**
- **Unit Tests**: Comprehensive business logic testing
- **Integration Tests**: Database and external service testing
- **UAT Tests**: User acceptance testing with Python UV
- **TestContainers**: Real database testing
- **Coverage Verification**: Automated coverage gates

## **Performance Optimization**

### **Caching Strategy**
- **Multi-Level**: L1 Caffeine (in-memory) + L2 Redis (distributed)
- **Cache-Aside Pattern**: Explicit cache management
- **TTL-Based**: Configurable expiration times

### **Database Performance**
- **HikariCP**: High-performance connection pooling
- **Strategic Indexing**: 28 indexes for query optimization
- **Batch Operations**: Configurable batch sizes for bulk operations
- **Connection Optimization**: Tuned pool settings and timeouts

### **JVM Configuration**
- **Z Garbage Collector**: Modern, low-latency GC
- **Generational ZGC**: Enhanced performance for production
- **Container Optimization**: Efficient resource usage

## **Deployment Architecture**

### **Containerization**
- **Docker Multi-stage Build**: Optimized image size
- **Eclipse Temurin JRE 21**: Production-grade runtime
- **Security Context**: Non-root user execution
- **Health Checks**: Comprehensive monitoring endpoints

### **Infrastructure Support**
- **Docker Compose**: Complete development environment
- **PostgreSQL 16**: Production database with Adminer
- **MailCatcher**: Email testing in development
- **Prometheus**: Metrics collection and monitoring

## **Billing System Accuracy**

### **Cost Calculation Formula**
```
total_cost_cents = total_requests × settings.cost_per_request_cents
```

### **Critical Accuracy Features**
- **Period-Level Aggregation**: Real-time updates on every successful request
- **Audit Trail**: Comprehensive request logging with immutable records
- **Settings-Driven**: Configurable cost per request
- **100% Accuracy Requirement**: Billing calculations must be mathematically precise

## **Key Architectural Strengths**

1. **Domain-Driven Design**: Clear bounded contexts with well-defined responsibilities
2. **Security-First**: Multiple layers of authentication and authorization
3. **Performance-Optimized**: Modern JVM, caching, and database optimization
4. **Quality-Driven**: Comprehensive code quality tools and testing
5. **Cloud-Ready**: Containerized deployment with monitoring
6. **Billing Precision**: Mathematically accurate cost calculation system
7. **Documentation-Rich**: Extensive API documentation and schema documentation

The system demonstrates enterprise-grade architecture with attention to security, performance, and accuracy - particularly in its billing system where 100% cost calculation accuracy is mandatory.