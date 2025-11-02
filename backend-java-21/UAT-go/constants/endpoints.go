package constants

// API endpoint constants
const (
	EndpointLogin               = "/api/customers/login"
	EndpointUserRegister        = "/api/customers/register"
	EndpointAdminInvites        = "/api/v1/admin/invites"
	EndpointAPITokens           = "/api/customers/tokens"
	EndpointCoreSolve           = "/api/core/solve"
	EndpointCoreTestSolve       = "/api/core/test-solve"
	EndpointBillingCurrent      = "/api/customers/billing/current"
	EndpointBillingPeriods      = "/api/customers/billing/periods"
	EndpointBillingPeriodDetail = "/api/customers/billing/periods/{periodId}"
	EndpointBillingHistory      = "/api/customers/billing/history"
	EndpointUsageSummary        = "/api/customers/usage/summary"
	EndpointUsageRequests       = "/api/customers/usage/requests"
	EndpointAdminBillingList    = "/api/v1/admin/billing"
	EndpointAdminMarkPaid       = "/api/v1/admin/billing/{periodId}/mark-paid"
	EndpointAdminMarkOverdue    = "/api/v1/admin/billing/{periodId}/mark-overdue"
	EndpointAdminWaive          = "/api/v1/admin/billing/{periodId}/waive"
	EndpointEmailVerify         = "/api/customers/verify-email"
	EndpointEmailResend         = "/api/customers/resend-verification"
	EndpointPasswordChange      = "/api/customers/password-change"
	EndpointUsersMe             = "/api/customers/me"
	EndpointHealth              = "/api/core/health"
)
