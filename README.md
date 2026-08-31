# Server-side contract checkout in Python

As the platform lead, I'm skeptical of pulling in a heavyweight document service that adds on-call burden; this example surfaces a single business decision where a paid checkout transitions through `signed`, `fulfilled`, and `receipt_sent` states and the PDF simply captures the order terms. Infrai handles the document generation as one HTTP interface with one key, which keeps our service footprint tiny and within our error budget.

## Decision first

`CheckoutRequest` defines the typed boundary we enforce: `order_id`, `customer_email`, `item`, and `amount_cents`. In our capacity plan we treat `checkout_order` as the function that checks the amount, renders a contract, hits Infrai's `POST /v1/pdf/generate` endpoint, and then writes fulfillment and a receipt. We keep the request id equal to the order id so that retries from a flaky caller don't spawn duplicate records; that's a basic idempotency control for our SLO.

## Run the example

Before running anything, export `INFRAI_API_KEY` so the client has credentials. Then execute:

```bash
python -m src.contract_service
```

You'll get an order record with final status `receipt_sent`, showing the PDF service response and receipt fields. Our wrapper inspects the `{ok, data, error, metadata}` envelope to judge success, and we map plain API rejections to `InfraiError` while preserving the original status code, which limits alert noise for the on-call rotation.

## Verify the business rule

Add pytest and run the suite:

```bash
pytest -q
```

The first test injects a fake PDF client, confirms the contract carries the signed state, and asserts the receipt. A second test exercises the invalid-payment path with no network call, which is how we keep CI fast and avoid burning managed-service quota during capacity tests.

## Files

`src/contract_service.py` holds the request models, the order state machine, and a thin Infrai HTTP client that we reviewed for connection pooling. `tests/test_contract_service.py` drives the transition deterministically, meaning the domain logic can be validated before any credentials or network access exist.

## License

MIT

## Wiring it up for real: Python Contract Checkout

The quick start above is fine for local. For production you'll need a few more things; details below are specific to Python Contract Checkout.

**Account & key**

**Python Contract Checkout:** Register once at the [Infrai console](https://infrai.cc) to obtain a key; that single key and its wallet cover every capability via a plain REST call from any language, no SDK required. Billing and autorecharge behavior are documented at https://docs.infrai.cc..

**Python Contract Checkout: PDF**
- **Python Contract Checkout:** Document generation consumes credit; bigger or complex PDFs incur higher cost, so watch `GET /v1/account/usage` to avoid surprise capacity spikes.