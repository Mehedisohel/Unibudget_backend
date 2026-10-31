from django.contrib.auth import authenticate, get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Budget, Transaction

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, max_length=150, trim_whitespace=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()

    def create(self, validated_data):
        name = validated_data.pop("name")
        email = validated_data.pop("email").strip().lower()
        password = validated_data.pop("password")
        return User.objects.create_user(
            username=email, email=email, password=password, first_name=name
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError({"detail": "Invalid email or password."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "This account is inactive."})
        refresh = RefreshToken.for_user(user)
        return {"user": user, "refresh": str(refresh), "access": str(refresh.access_token)}


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id", "title", "amount", "transaction_type", "category",
            "date", "payment_method",
        ]
        read_only_fields = ["id"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()

    EXPENSE_CATEGORIES = {"food", "transport", "bills", "study", "other"}

    class Meta:
        model = Budget
        fields = [
            "id", "category", "year", "month", "limit_amount",
            "spent", "remaining", "percentage_used", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "spent", "remaining", "percentage_used", "created_at", "updated_at"]

    def validate_category(self, value):
        if value not in self.EXPENSE_CATEGORIES:
            raise serializers.ValidationError("Budgets can only be set for expense categories.")
        return value

    def validate_month(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Month must be between 1 and 12.")
        return value

    def validate_year(self, value):
        if value < 2000 or value > 2200:
            raise serializers.ValidationError("Enter a valid year.")
        return value

    def validate_limit_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Budget limit must be greater than 0.")
        return value

    def _spent(self, obj):
        return Transaction.objects.filter(
            user=obj.user,
            transaction_type="expense",
            category=obj.category,
            date__year=obj.year,
            date__month=obj.month,
        ).aggregate(total=Sum("amount"))["total"] or 0

    def get_spent(self, obj):
        return self._spent(obj)

    def get_remaining(self, obj):
        return obj.limit_amount - self._spent(obj)

    def get_percentage_used(self, obj):
        spent = self._spent(obj)
        return round(float(spent / obj.limit_amount * 100), 2) if obj.limit_amount else 0


class FinancialSummarySerializer(serializers.Serializer):
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name", max_length=150, required=False)
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ["id", "name", "email"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = value.strip().lower()
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        if "email" in validated_data:
            email = validated_data["email"]
            instance.email = email
            # This project uses email as the login username.
            instance.username = email
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        user = self.context["request"].user
        try:
            password_validation.validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
