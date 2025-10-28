# TRC Platform Java Backend - Kubernetes Deployment Specification

## Overview

This document provides comprehensive Kubernetes deployment instructions and configurations for the TRC Platform Java backend. It includes containerization strategies, deployment manifests, CI/CD pipelines, and production deployment strategies.

## Table of Contents

1. [Containerization Strategy](#containerization-strategy)
2. [Kubernetes Deployment](#kubernetes-deployment)
3. [Development Environment Setup](#development-environment-setup)
4. [Production Deployment Strategy](#production-deployment-strategy)
5. [Blue-Green Deployment](#blue-green-deployment)
6. [CI/CD Pipeline](#ci-cd-pipeline)

---

## 1. Containerization Strategy

### 1.1 Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM openjdk:21-jdk-slim as builder

WORKDIR /app

# Copy Maven configuration
COPY pom.xml .
COPY .mvn .mvn
COPY mvnw .

# Download dependencies
RUN ./mvnw dependency:go-offline -B

# Copy source code
COPY src ./src

# Build application
RUN ./mvnw clean package -DskipTests

# Production stage
FROM openjdk:21-jre-slim

# Install required tools
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd --system spring && useradd --system --gid spring spring

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder /app/target/*.jar app.jar

# Change ownership
RUN chown spring:spring app.jar

# Switch to non-root user
USER spring:spring

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# Expose port
EXPOSE 8080

# JVM options
ENV JAVA_OPTS="-Xmx1g -Xms512m -XX:+UseG1GC -XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"

# Application startup
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

### 1.2 Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - DATABASE_URL=jdbc:postgresql://postgres:5432/trc_platform
      - DATABASE_USERNAME=trc_user
      - DATABASE_PASSWORD=trc_password
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - trc-network
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=trc_platform
      - POSTGRES_USER=trc_user
      - POSTGRES_PASSWORD=trc_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - trc-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - trc-network

volumes:
  postgres_data:
  redis_data:

networks:
  trc-network:
    driver: bridge
```

---

## 2. Kubernetes Deployment

### 2.1 Deployment Configuration

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trc-platform-backend
  namespace: trc-platform
  labels:
    app: trc-platform-backend
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: trc-platform-backend
  template:
    metadata:
      labels:
        app: trc-platform-backend
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus"
    spec:
      containers:
      - name: app
        image: trc-platform/backend:1.0.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: DATABASE_USERNAME
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: username
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: password
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
      terminationGracePeriodSeconds: 30
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - trc-platform-backend
              topologyKey: kubernetes.io/hostname
```

### 2.2 Service Configuration

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: trc-platform-backend-service
  namespace: trc-platform
  labels:
    app: trc-platform-backend
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: trc-platform-backend

---
apiVersion: v1
kind: Service
metadata:
  name: trc-platform-backend-headless
  namespace: trc-platform
  labels:
    app: trc-platform-backend
spec:
  type: ClusterIP
  clusterIP: None
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: trc-platform-backend
```

### 2.3 Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trc-platform-backend-hpa
  namespace: trc-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trc-platform-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

---

## 3. Development Environment Setup

### 3.1 Development Docker Compose

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
      - "5005:5005"  # Debug port
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - JAVA_TOOL_OPTIONS=-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005
    volumes:
      - .:/app
      - ~/.m2:/root/.m2
    depends_on:
      - postgres
      - redis
    networks:
      - trc-network

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=trc_platform_dev
      - POSTGRES_USER=trc_user
      - POSTGRES_PASSWORD=trc_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    networks:
      - trc-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - trc-network

volumes:
  postgres_dev_data:
  redis_dev_data:

networks:
  trc-network:
    driver: bridge
```

### 3.2 Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM openjdk:21-jdk-slim

WORKDIR /app

# Install Maven
RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*

# Copy Maven wrapper and configuration
COPY pom.xml .
COPY .mvn .mvn
COPY mvnw .

# Download dependencies (will be cached if pom.xml doesn't change)
RUN ./mvnw dependency:go-offline -B

# Expose debug port
EXPOSE 5005

# Run application in development mode
CMD ["./mvnw", "spring-boot:run"]
```

---

## 4. Production Deployment Strategy

### 4.1 Production Deployment Strategy

**Schema First Approach:**
1. **Deploy New Java Application**: Point to separate database schema
2. **Run Flyway Migrations**: Create all tables and indexes
3. **Data Validation**: Verify schema matches Django structure
4. **Data Sync**: One-time sync of user data if needed
5. **DNS Switch**: Point traffic to Java application
6. **Monitor**: Ensure everything works as expected
7. **Retire Django**: Decommission old Django application

**Zero-Downtime Migration:**
```yaml
# k8s/migration-strategy.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: trc-platform-migration
spec:
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 10m}
      - setWeight: 50
      - pause: {duration: 10m}
      - setWeight: 100
  replicas: 5
```

---

## 5. Blue-Green Deployment

### 5.1 Blue-Green Deployment Configuration

```yaml
# k8s/blue-green-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: trc-platform-backend
  namespace: trc-platform
spec:
  replicas: 5
  strategy:
    blueGreen:
      activeService: trc-platform-backend-active
      previewService: trc-platform-backend-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: trc-platform-backend-preview
      postPromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: trc-platform-backend-active
  selector:
    matchLabels:
      app: trc-platform-backend
  template:
    metadata:
      labels:
        app: trc-platform-backend
    spec:
      containers:
      - name: app
        image: trc-platform/backend:1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### 5.2 Production Deployment Steps

**Step 1: Schema Validation**
```bash
# Validate Flyway migrations before deployment
./mvnw flyway:validate -Dflyway.url=$DATABASE_URL -Dflyway.user=$DATABASE_USER -Dflyway.password=$DATABASE_PASSWORD
```

**Step 2: Gradual Traffic Routing**
```yaml
# Deploy with 20% traffic to new version
kubectl patch rollout trc-platform-backend -p '{"spec":{"strategy":{"blueGreen":{"prePromotionSteps":[{"setWeight":20},{"pause":{"duration":"10m"}}]}}}}'
```

**Step 3: Health Checks and Monitoring**
```bash
# Monitor application health
kubectl get rollout trc-platform-backend -n trc-platform
kubectl logs -f deployment/trc-platform-backend-preview -n trc-platform
```

**Step 4: Full Cut-over**
```bash
# Promote new version to 100%
kubectl patch rollout trc-platform-backend -p '{"spec":{"strategy":{"blueGreen":{"autoPromotionEnabled":true}}}}'
```

---

## 6. CI/CD Pipeline

### 6.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: trc-platform/backend

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_USER: postgres
          POSTGRES_DB: trc_platform_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up JDK 21
      uses: actions/setup-java@v4
      with:
        java-version: '21'
        distribution: 'temurin'

    - name: Cache Maven dependencies
      uses: actions/cache@v3
      with:
        path: ~/.m2
        key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
        restore-keys: ${{ runner.os }}-m2

    - name: Run tests
      env:
        DATABASE_URL: jdbc:postgresql://localhost:5432/trc_platform_test
        DATABASE_USERNAME: postgres
        DATABASE_PASSWORD: postgres
        REDIS_URL: redis://localhost:6379
      run: ./mvnw clean test

    - name: Generate test report
      uses: dorny/test-reporter@v1
      if: success() || failure()
      with:
        name: Maven Tests
        path: target/surefire-reports/*.xml
        reporter: java-junit

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-

    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - uses: actions/checkout@v4

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.29.0'

    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig

    - name: Deploy to Kubernetes
      run: |
        export KUBECONFIG=kubeconfig

        # Update image tag in deployment
        sed -i "s|trc-platform/backend:.*|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:main-${{ github.sha }}|" k8s/deployment.yaml

        # Apply configurations
        kubectl apply -f k8s/ -n trc-platform

        # Wait for rollout
        kubectl rollout status deployment/trc-platform-backend -n trc-platform --timeout=300s
```

---

## Additional Resources

### Required Kubernetes Manifests

For a complete deployment, you will also need to create:

1. **Namespace Configuration**
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: trc-platform
   ```

2. **ConfigMap for Application Configuration**
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
     namespace: trc-platform
   data:
     redis-url: "redis://redis-service:6379"
     app-domain: "https://app.trc-platform.com"
   ```

3. **Secrets for Sensitive Data**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: database-secret
     namespace: trc-platform
   type: Opaque
   data:
     url: <base64-encoded-database-url>
     username: <base64-encoded-username>
     password: <base64-encoded-password>
   ```

4. **Ingress Configuration**
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: trc-platform-backend-ingress
     namespace: trc-platform
     annotations:
       kubernetes.io/ingress.class: nginx
       cert-manager.io/cluster-issuer: letsencrypt-prod
   spec:
     tls:
     - hosts:
       - api.trc-platform.com
       secretName: trc-platform-tls
     rules:
     - host: api.trc-platform.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: trc-platform-backend-service
               port:
                 number: 80
   ```

### Deployment Prerequisites

1. **Kubernetes Cluster**: Version 1.29+ with required addons
2. **Ingress Controller**: NGINX or similar
3. **Certificate Manager**: For SSL/TLS certificates
4. **Monitoring Stack**: Prometheus and Grafana
5. **Logging Stack**: ELK or similar for centralized logging

### Environment Variables

The application expects the following environment variables in production:

- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_USERNAME`: Database username
- `DATABASE_PASSWORD`: Database password
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key
- `SPRING_PROFILES_ACTIVE`: Set to "production"

### Security Considerations

1. **Network Policies**: Implement proper network segmentation
2. **Pod Security Policies**: Use restrictive security contexts
3. **RBAC**: Implement proper role-based access control
4. **Secrets Management**: Use external secret stores when possible
5. **Image Security**: Use signed images and vulnerability scanning