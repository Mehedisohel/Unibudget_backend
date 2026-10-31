from django.contrib import admin
from .models import Budget, Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "amount", "transaction_type", "category", "date", "payment_method", "user")
    list_filter = ("transaction_type", "category", "date")
    search_fields = ("title", "payment_method", "user__email")
    ordering = ("-date",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "year", "month", "limit_amount")
    list_filter = ("year", "month", "category")
    search_fields = ("user__email",)
