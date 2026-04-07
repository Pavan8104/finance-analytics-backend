"""
Tests for the analytics report endpoint.

Covers:
  - Viewer role cannot access analytics (403)
  - Analyst role can access analytics (200)
  - Admin role can access analytics (200)
  - Report contains correct totals
  - Report has correct structure (category breakdowns, monthly)
  - Empty report for user with no transactions
"""
import pytest


INCOME_TX = {"amount": "3000.00", "type": "income", "category": "Salary"}
EXPENSE_TX = {"amount": "500.00", "type": "expense", "category": "Groceries"}


class TestAnalyticsRBAC:

    def test_viewer_cannot_access_report(self, viewer_client):
        """Viewers do NOT have access to analytics — 403 Forbidden."""
        response = viewer_client.get("/api/v1/analytics/report")
        assert response.status_code == 403

    def test_analyst_can_access_report(self, analyst_client):
        """Analysts CAN access analytics — 200 OK."""
        response = analyst_client.get("/api/v1/analytics/report")
        assert response.status_code == 200

    def test_admin_can_access_report(self, admin_client):
        """Admins CAN access analytics — 200 OK."""
        response = admin_client.get("/api/v1/analytics/report")
        assert response.status_code == 200

    def test_unauthenticated_cannot_access_report(self, client):
        """Unauthenticated requests return 401."""
        response = client.get("/api/v1/analytics/report")
        assert response.status_code == 401


class TestAnalyticsReport:

    def test_empty_report_for_new_user(self, analyst_client):
        """A user with no transactions gets a zeroed report."""
        response = analyst_client.get("/api/v1/analytics/report")
        assert response.status_code == 200
        body = response.json()
        assert float(body["total_income"]) == 0.0
        assert float(body["total_expenses"]) == 0.0
        assert float(body["balance"]) == 0.0
        assert body["transaction_count"] == 0
        assert body["income_by_category"] == []
        assert body["expenses_by_category"] == []
        assert body["monthly_breakdown"] == []

    def test_report_correct_totals(self, analyst_client):
        """Report totals must match the sum of created transactions."""
        analyst_client.post("/api/v1/transactions/", json=INCOME_TX)
        analyst_client.post("/api/v1/transactions/", json=EXPENSE_TX)

        response = analyst_client.get("/api/v1/analytics/report")
        assert response.status_code == 200
        body = response.json()

        assert float(body["total_income"]) == 3000.00
        assert float(body["total_expenses"]) == 500.00
        assert float(body["balance"]) == 2500.00
        assert body["transaction_count"] == 2

    def test_report_has_category_breakdowns(self, analyst_client):
        """Report must include category breakdowns for income and expenses."""
        analyst_client.post("/api/v1/transactions/", json=INCOME_TX)
        analyst_client.post("/api/v1/transactions/", json=EXPENSE_TX)

        response = analyst_client.get("/api/v1/analytics/report")
        body = response.json()

        assert len(body["income_by_category"]) == 1
        assert body["income_by_category"][0]["category"] == "Salary"
        assert float(body["income_by_category"][0]["total_amount"]) == 3000.00
        assert body["income_by_category"][0]["percentage"] == 100.0

        assert len(body["expenses_by_category"]) == 1
        assert body["expenses_by_category"][0]["category"] == "Groceries"

    def test_report_has_monthly_breakdown(self, analyst_client):
        """Report must include a monthly breakdown list."""
        analyst_client.post("/api/v1/transactions/", json=INCOME_TX)

        response = analyst_client.get("/api/v1/analytics/report")
        body = response.json()

        assert "monthly_breakdown" in body
        assert len(body["monthly_breakdown"]) >= 1
        month = body["monthly_breakdown"][0]
        assert "month" in month
        assert "income" in month
        assert "expense" in month
        assert "net" in month

    def test_report_data_isolated_per_user(self, analyst_client, analyst_user, db):
        """Analytics report must only include the authenticated user's transactions."""
        # Clear the module-level TTLCache to prevent bleed from previous test
        from app.services.analytics_service import _cache, _cache_lock
        with _cache_lock:
            _cache.clear()

        from app.models.user import User, RoleEnum
        from app.models.transaction import Transaction, TransactionType
        from app.core.security import get_password_hash

        # Create a completely separate user with a transaction in the same DB
        other_user = User(
            email="other@test.com",
            hashed_password=get_password_hash("Other1234!"),
            role=RoleEnum.viewer,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Create a transaction owned by the other user, NOT the analyst
        tx = Transaction(
            amount=3000.00,
            type=TransactionType.income,
            category="Salary",
            owner_id=other_user.id,
        )
        db.add(tx)
        db.commit()

        # Analyst has no transactions — their report should show zero
        response = analyst_client.get("/api/v1/analytics/report")
        assert response.status_code == 200
        body = response.json()
        assert body["transaction_count"] == 0
        assert float(body["total_income"]) == 0.0
