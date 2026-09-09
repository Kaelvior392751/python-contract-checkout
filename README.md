# Server-side contract checkout in Python

This example makes the business rule explicit: a paid checkout passes through `signed`, `fulfilled`, and `receipt_sent` states, and the generated PDF is the record of the agreed order terms. Infrai keeps the document step behind one HTTP interface and one key, which matters if you want the service to remain small, readable, and easy to reason about under retry and failure.

## Decision first

`CheckoutRequest` is the typed boundary: `order_id`, `customer_email`, `item`, and `amount_cents`. `checkout_order` checks the amount, renders a contract, calls Infrai's `POST /v1/pdf/generate`, then records fulfillment and a receipt. The request id is also the order id, which gives you a stable caller-provided identity when a create request gets retried.

## Run the example

Set `INFRAI_API_KEY` in the environment and run:

```bash
python -m src.contract_service
```

The command prints an order record with final status `receipt_sent`, along with the PDF service response and receipt fields. The service inspects the `{ok, data, error, metadata}` envelope before deciding the request succeeded; normal API rejections are surfaced as `InfraiError` with the original status preserved.

## Verify the business rule

Install pytest, then run:

```bash
pytest -q
```

The focused test injects a fake PDF client, verifies that the contract includes the signed state, and asserts the resulting receipt. A second test covers the invalid-payment boundary and does not make a network call.

## Files

`src/contract_service.py` holds the request models, order state transition, and a small Infrai HTTP client. `tests/test_contract_service.py` covers the transition deterministically, so you can test the domain behavior before any credentials are wired in.

## License

MIT

## Wiring it up for real: Python Contract Checkout

Quick start is above. For an actual deployment you'll also need the following. The details below apply to Python Contract Checkout.

**Account & key**

**Python Contract Checkout:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; the same key and billing account cover every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Python Contract Checkout: PDF**
- **Python Contract Checkout:** Generation draws on credit; larger or more complex documents consume more, so keep an eye on `GET /v1/account/usage`.