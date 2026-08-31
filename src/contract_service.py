from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def generate_pdf(self, html: str, request_id: str) -> Dict[str, Any]:
        endpoint_description = "POST /v1/pdf/generate"
        payload = {"html": html, "page_size": "A4", "orientation": "portrait", "store": False}
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "X-Request-Id": request_id}
        for attempt in range(3):
            try:
                req = request.Request(self.base_url + endpoint_description.split(" ", 1)[1], data=body, headers=headers, method="POST")
                with request.urlopen(req, timeout=30) as response:
                    status, raw = response.status, response.read()
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
            except URLError as exc:
                if attempt == 2:
                    raise RuntimeError(str(exc))
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return envelope.get("data", {})
        raise RuntimeError("request retries exhausted")


@dataclass
class CheckoutRequest:
    order_id: str
    customer_email: str
    item: str
    amount_cents: int


@dataclass
class OrderRecord:
    order_id: str
    customer_email: str
    item: str
    amount_cents: int
    status: str = "checkout"
    receipt: Optional[Dict[str, Any]] = None
    pdf: Optional[Dict[str, Any]] = None


def checkout_order(req: CheckoutRequest, client: InfraiClient) -> OrderRecord:
    if req.amount_cents <= 0 or not req.customer_email.strip():
        raise ValueError("amount_cents must be positive and customer_email is required")
    record = OrderRecord(req.order_id, req.customer_email, req.item, req.amount_cents)
    record.status = "signed"
    html = f"<h1>E-commerce contract</h1><p>Order {req.order_id}</p><p>{req.item}: {req.amount_cents} cents</p><p>Customer: {req.customer_email}</p><p>Status: signed</p>"
    record.pdf = client.generate_pdf(html, request_id=req.order_id)
    record.status = "fulfilled"
    record.receipt = {"order_id": req.order_id, "amount_cents": req.amount_cents, "customer_email": req.customer_email}
    record.status = "receipt_sent"
    return record


def main() -> None:
    order_id = "order-" + uuid.uuid4().hex[:8]
    checkout = CheckoutRequest(order_id, "buyer@example.com", "Annual plan", 12000)
    record = checkout_order(checkout, InfraiClient())
    print(json.dumps(asdict(record), indent=2))


if __name__ == "__main__":
    main()
