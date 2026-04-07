"""
Tests for transaction CRUD endpoints.

Covers:
  - Create transaction (201)
  - List transactions (pagination, filters)
  - Get single transaction
  - Update transaction
  - Delete transaction (204)
  - Ownership isolation (users cannot access each other's transactions)
  - Input validation (negative amount, empty category)
"""
import pytest


INCOME_PAYLOAD = {
    "amount": "1500.00",
    "type": "income",
    "category": "Salary",
    "notes": "Monthly pay",
}

EXPENSE_PAYLOAD = {
    "amount": "200.50",
    "type": "expense",
    "category": "Groceries",
    "notes": "Weekly shop",
}


class TestCreateTransaction:

    def test_create_income_returns_201(self, viewer_client):
        response = viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        assert response.status_code == 201
        body = response.json()
        assert body["amount"] == "1500.00"
        assert body["type"] == "income"
        assert body["category"] == "Salary"

    def test_create_expense_returns_201(self, viewer_client):
        response = viewer_client.post("/api/v1/transactions/", json=EXPENSE_PAYLOAD)
        assert response.status_code == 201
        assert response.json()["type"] == "expense"

    def test_unauthenticated_cannot_create(self, client):
        response = client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        assert response.status_code == 401

    def test_negative_amount_rejected(self, viewer_client):
        payload = {**INCOME_PAYLOAD, "amount": "-100.00"}
        response = viewer_client.post("/api/v1/transactions/", json=payload)
        assert response.status_code == 422

    def test_zero_amount_rejected(self, viewer_client):
        payload = {**INCOME_PAYLOAD, "amount": "0"}
        response = viewer_client.post("/api/v1/transactions/", json=payload)
        assert response.status_code == 422

    def test_invalid_type_rejected(self, viewer_client):
        payload = {**INCOME_PAYLOAD, "type": "gift"}
        response = viewer_client.post("/api/v1/transactions/", json=payload)
        assert response.status_code == 422


class TestListTransactions:

    def test_list_returns_own_transactions_only(self, viewer_client, db, viewer_user, admin_user):
        """Users must only see their own transactions."""
        from app.models.transaction import Transaction, TransactionType

        # Create a transaction for viewer via HTTP
        viewer_resp = viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        viewer_tx_id = viewer_resp.json()["id"]

        # Create a transaction for admin directly in DB (different owner_id)
        admin_tx = Transaction(
            amount=200.50,
            type=TransactionType.expense,
            category="Groceries",
            notes="Admin only",
            owner_id=admin_user.id,
        )
        db.add(admin_tx)
        db.commit()
        db.refresh(admin_tx)

        # Viewer should only see their own
        response = viewer_client.get("/api/v1/transactions/")
        assert response.status_code == 200
        body = response.json()
        item_ids = [item["id"] for item in body["items"]]
        assert viewer_tx_id in item_ids
        assert admin_tx.id not in item_ids

    def test_pagination_works(self, viewer_client):
        # Create 5 transactions
        for i in range(5):
            viewer_client.post(
                "/api/v1/transactions/",
                json={**INCOME_PAYLOAD, "amount": str(100 + i)},
            )
        response = viewer_client.get("/api/v1/transactions/?skip=0&limit=3")
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 3
        assert body["total"] == 5
        assert body["pages"] == 2
        assert body["has_next"] is True
        assert body["has_prev"] is False
        assert body["next_skip"] == 3

    def test_filter_by_type(self, viewer_client):
        viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        viewer_client.post("/api/v1/transactions/", json=EXPENSE_PAYLOAD)

        response = viewer_client.get("/api/v1/transactions/?type=expense")
        assert response.status_code == 200
        items = response.json()["items"]
        assert all(t["type"] == "expense" for t in items)

    def test_filter_by_category(self, viewer_client):
        viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        viewer_client.post("/api/v1/transactions/", json=EXPENSE_PAYLOAD)

        response = viewer_client.get("/api/v1/transactions/?category=salary")
        assert response.status_code == 200
        items = response.json()["items"]
        assert all(t["category"].lower() == "salary" for t in items)

    def test_empty_list_for_new_user(self, viewer_client):
        response = viewer_client.get("/api/v1/transactions/")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestGetTransaction:

    def test_get_own_transaction(self, viewer_client):
        create_resp = viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        tx_id = create_resp.json()["id"]

        response = viewer_client.get(f"/api/v1/transactions/{tx_id}")
        assert response.status_code == 200
        assert response.json()["id"] == tx_id

    def test_get_other_users_transaction_returns_404(self, viewer_client, db, admin_user):
        """Ownership isolation: viewer cannot fetch admin's transaction by ID."""
        from app.models.transaction import Transaction, TransactionType

        # Create admin's transaction directly in DB
        admin_tx = Transaction(
            amount=200.50,
            type=TransactionType.expense,
            category="Admin Expense",
            owner_id=admin_user.id,
        )
        db.add(admin_tx)
        db.commit()
        db.refresh(admin_tx)

        response = viewer_client.get(f"/api/v1/transactions/{admin_tx.id}")
        assert response.status_code == 404

    def test_get_nonexistent_returns_404(self, viewer_client):
        response = viewer_client.get("/api/v1/transactions/99999")
        assert response.status_code == 404


class TestUpdateTransaction:

    def test_update_amount_and_notes(self, viewer_client):
        create_resp = viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        tx_id = create_resp.json()["id"]

        response = viewer_client.put(
            f"/api/v1/transactions/{tx_id}",
            json={"amount": "2000.00", "notes": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Updated"

    def test_cannot_update_others_transaction(self, viewer_client, db, admin_user):
        from app.models.transaction import Transaction, TransactionType

        admin_tx = Transaction(
            amount=200.50,
            type=TransactionType.expense,
            category="Admin Expense",
            owner_id=admin_user.id,
        )
        db.add(admin_tx)
        db.commit()
        db.refresh(admin_tx)

        response = viewer_client.put(
            f"/api/v1/transactions/{admin_tx.id}", json={"notes": "Hijack"}
        )
        assert response.status_code == 404


class TestDeleteTransaction:

    def test_delete_own_transaction_returns_204(self, viewer_client):
        create_resp = viewer_client.post("/api/v1/transactions/", json=INCOME_PAYLOAD)
        tx_id = create_resp.json()["id"]

        response = viewer_client.delete(f"/api/v1/transactions/{tx_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_resp = viewer_client.get(f"/api/v1/transactions/{tx_id}")
        assert get_resp.status_code == 404

    def test_cannot_delete_others_transaction(self, viewer_client, db, admin_user):
        from app.models.transaction import Transaction, TransactionType

        admin_tx = Transaction(
            amount=200.50,
            type=TransactionType.expense,
            category="Admin Expense",
            owner_id=admin_user.id,
        )
        db.add(admin_tx)
        db.commit()
        db.refresh(admin_tx)

        response = viewer_client.delete(f"/api/v1/transactions/{admin_tx.id}")
        assert response.status_code == 404
