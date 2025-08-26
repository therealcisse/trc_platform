from django.urls import path

from .views import (
    ApiTokenRevokeView,
    ApiTokenView,
    BillingPeriodDetailView,
    BillingPeriodsListView,
    ChangePasswordView,
    CurrentBillingPeriodView,
    CurrentUserView,
    LoginView,
    LogoutView,
    RegisterView,
    UsageRequestsView,
    UsageSummaryView,
    VerifyEmailView,
)

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", CurrentUserView.as_view(), name="current-user"),
    path("verify-email", VerifyEmailView.as_view(), name="verify-email"),
    path("password/change", ChangePasswordView.as_view(), name="change-password"),
    path("tokens", ApiTokenView.as_view(), name="tokens"),
    path("tokens/<uuid:pk>", ApiTokenRevokeView.as_view(), name="token-revoke"),
    path("usage/requests", UsageRequestsView.as_view(), name="usage-requests"),
    path("usage/summary", UsageSummaryView.as_view(), name="usage-summary"),
    # Billing endpoints
    path("billing/current", CurrentBillingPeriodView.as_view(), name="billing-current"),
    path("billing/periods", BillingPeriodsListView.as_view(), name="billing-periods"),
    path(
        "billing/periods/<uuid:period_id>",
        BillingPeriodDetailView.as_view(),
        name="billing-period-detail",
    ),
]
