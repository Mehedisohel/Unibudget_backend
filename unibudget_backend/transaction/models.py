from django.conf import settings
from django.db import models


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ("income", "Income"),
        ("expense", "Expense"),
    )

    CATEGORY_CHOICES = (
        ("food", "Food"),
        ("transport", "Transport"),
        ("bills", "Bills"),
        ("study", "Study"),
        ("other", "Other"),
        ("salary", "Salary"),
        ("allowance", "Allowance"),
        ("gift", "Gift"),
        ("refund", "Refund"),
    )

    PAYMENT_CHOICES = (
        ("cash", "Cash"),
        ("bkash", "bKash"),
        ("debit_card", "Debit Card"),
        ("bank_transfer", "Bank Transfer"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    date = models.DateField()
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True
    )

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.title} - {self.amount}"


class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=Transaction.CATEGORY_CHOICES)
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    limit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "category"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "year", "month"],
                name="unique_user_monthly_category_budget",
            ),
        ]

    def __str__(self):
        return f"{self.user_id}: {self.category} {self.year}-{self.month:02d}"
