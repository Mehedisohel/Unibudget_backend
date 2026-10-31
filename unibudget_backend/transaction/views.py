from datetime import date

from django.contrib.auth import update_session_auth_hash
from django.db.models import Q, Sum
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import Budget, Transaction
from .serializers import (
    BudgetSerializer,
    ChangePasswordSerializer,
    FinancialSummarySerializer,
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    TransactionSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Account created successfully.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {"id": user.id, "name": user.first_name, "email": user.email},
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(
            {
                "message": "Login successful.",
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"],
                "user": {"id": user.id, "name": user.first_name, "email": user.email},
            },
            status=status.HTTP_200_OK,
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            # Ensure a token supplied here belongs to the authenticated user.
            if str(token.get("user_id")) != str(request.user.pk):
                return Response(
                    {"error": "Refresh token does not belong to the authenticated user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token.blacklist()
        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user)
        params = self.request.query_params

        transaction_type = params.get("transaction_type")
        category = params.get("category")
        date_from = params.get("date_from")
        date_to = params.get("date_to")

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if category:
            queryset = queryset.filter(category=category)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expense_categories = {"food", "transport", "bills", "study", "other"}
        categories = [
            {
                "value": value,
                "label": label,
                "type": "expense" if value in expense_categories else "income",
            }
            for value, label in Transaction.CATEGORY_CHOICES
        ]
        requested_type = request.query_params.get("type")
        if requested_type in {"income", "expense"}:
            categories = [item for item in categories if item["type"] == requested_type]
        elif requested_type:
            return Response(
                {"detail": "type must be either 'income' or 'expense'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(categories)


class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Budget.objects.filter(user=self.request.user)
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        category = self.request.query_params.get("category")
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FinancialSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Transaction.objects.filter(user=request.user)
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        summary = queryset.aggregate(
            total_income=Sum("amount", filter=Q(transaction_type="income")),
            total_expense=Sum("amount", filter=Q(transaction_type="expense")),
        )
        total_income = summary["total_income"] or 0
        total_expense = summary["total_expense"] or 0
        serializer = FinancialSummarySerializer(
            {
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense,
            }
        )
        return Response(serializer.data)


class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        try:
            year = int(request.query_params.get("year", today.year))
            month = int(request.query_params.get("month", today.month))
            if not 1 <= month <= 12 or not 2000 <= year <= 2200:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"detail": "Provide a valid year and month (month 1-12)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Transaction.objects.filter(
            user=request.user, date__year=year, date__month=month
        )
        totals = queryset.aggregate(
            total_income=Sum("amount", filter=Q(transaction_type="income")),
            total_expense=Sum("amount", filter=Q(transaction_type="expense")),
        )
        income = totals["total_income"] or 0
        expense = totals["total_expense"] or 0
        category_rows = (
            queryset.filter(transaction_type="expense")
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        return Response(
            {
                "year": year,
                "month": month,
                "total_income": income,
                "total_expense": expense,
                "balance": income - expense,
                "expenses_by_category": list(category_rows),
                "transaction_count": queryset.count(),
            }
        )
