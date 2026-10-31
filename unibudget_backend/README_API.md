# UniBudget Django REST Framework backend

## Apply database migrations
From the folder containing `manage.py`, run:

```bash
python manage.py migrate
python manage.py runserver
```

## Authentication
- `POST /register/`
- `POST /login/`
- `POST /refresh/`
- `GET /me/` (Bearer access token)
- `PATCH /me/` (Bearer access token)
- `POST /change-password/` (Bearer access token)
- `POST /logout/` (Bearer access token; JSON body contains refresh token)

## Transactions
- `GET, POST /api/transactions/`
- `GET, PUT, PATCH, DELETE /api/transactions/<id>/`
- Optional list filters: `transaction_type`, `category`, `date_from`, `date_to`
- The server automatically associates new transactions with the authenticated user.

## Categories
- `GET /categories/`
- Optional filter: `?type=income` or `?type=expense`

Categories are currently predefined in `Transaction.CATEGORY_CHOICES`; this endpoint lists them. It is not a database-backed custom-category manager.

## Budgets
- `GET, POST /api/budgets/`
- `GET, PUT, PATCH, DELETE /api/budgets/<id>/`
- Optional filters: `year`, `month`, `category`
- Budgets are scoped to the authenticated user and one category per month.
- Response includes calculated `spent`, `remaining`, and `percentage_used`.

## Financial summaries
- `GET /summary/` (optional `date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`)
- `GET /reports/monthly/?year=2026&month=10`

All user data endpoints require `Authorization: Bearer <access_token>`.

## Before deployment
- Replace the development `SECRET_KEY` with an environment variable and set `DEBUG=False`.
- Configure `ALLOWED_HOSTS` and CORS for the real deployment/frontend origin.
- Use HTTPS in production.
