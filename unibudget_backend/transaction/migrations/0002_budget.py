from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("transaction", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Budget",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("food", "Food"), ("transport", "Transport"), ("bills", "Bills"), ("study", "Study"), ("other", "Other"), ("salary", "Salary"), ("allowance", "Allowance"), ("gift", "Gift"), ("refund", "Refund")], max_length=20)),
                ("year", models.PositiveSmallIntegerField()),
                ("month", models.PositiveSmallIntegerField()),
                ("limit_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-year", "-month", "category"]},
        ),
        migrations.AddConstraint(
            model_name="budget",
            constraint=models.UniqueConstraint(fields=("user", "category", "year", "month"), name="unique_user_monthly_category_budget"),
        ),
    ]
