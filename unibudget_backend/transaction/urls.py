from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    BudgetViewSet,
    CategoryListView,
    ChangePasswordView,
    FinancialSummaryView,
    LoginView,
    LogoutView,
    MeView,
    MonthlyReportView,
    RegisterView,
    TransactionViewSet,
)

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("budgets", BudgetViewSet, basename="budget")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("summary/", FinancialSummaryView.as_view(), name="financial-summary"),
    path("reports/monthly/", MonthlyReportView.as_view(), name="monthly-report"),
    path("api/", include(router.urls)),
]
