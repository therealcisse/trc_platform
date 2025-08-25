from django.urls import path

from .views import (
    ApiTokenCreateView,
    ApiTokenListView,
    ApiTokenRevokeView,
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
from .views_debug import DebugAuthView  # TODO: Remove in production

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("me", CurrentUserView.as_view(), name="current-user"),
    path("debug/auth", DebugAuthView.as_view(), name="debug-auth"),  # TODO: Remove in production
    path("verify-email", VerifyEmailView.as_view(), name="verify-email"),
    path("password/change", ChangePasswordView.as_view(), name="change-password"),
    path("tokens", ApiTokenListView.as_view(), name="token-list"),
    path("tokens", ApiTokenCreateView.as_view(), name="token-create"),
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
