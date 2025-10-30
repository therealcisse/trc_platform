# Code Quality and Formatting

This project includes comprehensive code quality and formatting tools to ensure consistent, high-quality code.

## Tools Included

### 1. Spotless - Code Formatting
Automatically formats Java code using Google Java Style and removes unused imports.

**Commands:**
- `mvn spotless:check` - Check if code is properly formatted
- `mvn spotless:apply` - Apply formatting to all source files
- `mvn spotless:check` runs automatically during `validate` phase

### 2. JaCoCo - Code Coverage
Measures test coverage and generates reports.

**Commands:**
- `mvn test` - Runs tests and generates coverage report
- `mvn jacoco:report` - Generate coverage report
- `mvn jacoco:check` - Check coverage thresholds (currently 70% instruction coverage)

**Reports:**
- HTML report: `target/site/jacoco/index.html`
- XML report: `target/site/jacoco/jacoco.xml`

### 3. PMD - Static Analysis
Analyzes code for potential issues and bad practices.

**Commands:**
- `mvn pmd:check` - Run PMD analysis (fails on violations)
- `mvn pmd:cpd-check` - Check for duplicate code
- `mvn pmd:pmd` - Generate PMD report

**Reports:**
- HTML report: `target/site/pmd.html`
- CPD report: `target/site/cpd.html`

### 4. SpotBugs - Bug Detection
Detects potential bugs and security vulnerabilities.

**Commands:**
- `mvn spotbugs:check` - Run SpotBugs analysis
- `mvn spotbugs:gui` - Launch SpotBugs GUI for detailed analysis

**Reports:**
- XML report: `target/spotbugsXml.xml`
- HTML report: `target/site/spotbugs.html`

## Configuration Files

- `.editorconfig` - Basic editor configuration
- `pmd-rules.xml` - Custom PMD rule set
- `spotbugs-exclude.xml` - SpotBugs exclusions

## Maven Lifecycle Integration

All quality checks run automatically during the build process:

1. **validate** - Spotless formatting check
2. **compile** - PMD analysis
3. **test** - JaCoCo coverage, SpotBugs analysis

## IDE Integration

### IntelliJ IDEA
1. Install the following plugins:
   - Spotless
   - JaCoCo
   - PMD Plugin
   - SpotBugs

2. Enable import formatting and code style from Google Java Style

### VS Code
1. Install the following extensions:
   - Extension Pack for Java
   - SonarLint (for additional code quality checks)

## CI/CD Integration

These tools are configured to fail the build on quality violations, ensuring consistent code quality in CI/CD pipelines.

### Coverage Requirements
- Minimum 70% instruction coverage (configurable in pom.xml)

### Customization
- Adjust PMD rules in `pmd-rules.xml`
- Modify SpotBugs exclusions in `spotbugs-exclude.xml`
- Change JaCoCo coverage thresholds in pom.xml
- Customize Spotless formatting rules in pom.xml