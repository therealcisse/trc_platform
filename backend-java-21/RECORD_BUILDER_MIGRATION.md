# Java Records to Lombok @Builder Migration

## Project Status
- **Build Tool**: Gradle
- **Lombok Version**: Already configured (lines 71-72 in build.gradle)
- **Java Version**: 21
- **Total Records Found**: 18 files

## Migration Plan

### Phase 1: Prerequisites ✅
- [x] Lombok dependency verified
- [x] Annotation processor configured
- [x] IDE plugin check needed

### Phase 2: Record Identification ✅
Records found in the following files:
1. `core/dto/SolveResponse.java` - Has custom compact constructor
2. `admin/dto/CreateInviteCodeRequest.java`
3. `admin/dto/BillingPeriodAdminResponse.java`
4. `admin/dto/MarkOverdueRequest.java`
5. `admin/dto/MarkPaidRequest.java`
6. `admin/dto/InviteCodeResponse.java`
7. `admin/dto/MarkWaivedRequest.java`
8. `usage/dto/BillingPeriodResponse.java`
9. `usage/dto/CurrentBillingResponse.java`
10. `usage/dto/BillingPeriodDetailDto.java`
11. `users/dto/RegistrationRequest.java`
12. `users/dto/ApiTokenResponse.java` - Uses Optional
13. `users/dto/CreateApiTokenRequest.java`
14. `users/dto/LoginRequest.java`
15. `users/dto/ResendVerificationRequest.java`
16. `users/dto/EmailVerificationRequest.java`
17. `users/dto/PasswordChangeRequest.java`
18. `monitoring/dto/HealthResponse.java`

### Phase 3: Migration Steps
- [ ] Add @Builder to all records
- [ ] Handle special cases (custom constructors, defaults, Optional fields)
- [ ] Add @Jacksonized for JSON deserialization compatibility

### Phase 4: Testing
- [ ] Compile project
- [ ] Run existing tests
- [ ] Verify builder methods work
- [ ] Check JSON serialization/deserialization

### Phase 5: Validation
- [ ] IDE recognition check
- [ ] Code quality tools pass
- [ ] Integration tests pass

## Special Cases Identified

### Records with Custom Logic
1. **SolveResponse** - Has compact constructor for defensive copying
   - Keep compact constructor
   - Add @Builder annotation

2. **ApiTokenResponse** - Uses Optional<String>
   - @Builder works with Optional
   - No special handling needed

## Migration Commands

```bash
# Compile and verify
./gradlew clean compileJava

# Run tests
./gradlew test

# Run code quality checks
./gradlew check

# Format code
./gradlew spotlessApply
```

## Rollback Plan
All changes can be reverted via git:
```bash
git checkout src/
```
