import os

import pytest

from src.contract_service import CheckoutRequest, checkout_order


class FakeClient:
    def generate_pdf(self, html, request_id):
        assert request_id == "order-42"
        assert "Status: signed" in html
        return {"document_id": "pdf-42"}


def test_checkout_transitions_to_receipt_sent():
    req = CheckoutRequest("order-42", "buyer@example.com", "Notebook", 2500)
    result = checkout_order(req, FakeClient())
    assert result.status == "receipt_sent"
    assert result.receipt["amount_cents"] == 2500
    assert result.pdf["document_id"] == "pdf-42"


def test_checkout_rejects_invalid_amount():
    with pytest.raises(ValueError):
        checkout_order(CheckoutRequest("x", "buyer@example.com", "Item", 0), FakeClient())
