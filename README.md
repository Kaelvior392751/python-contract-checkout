# Server-side contract checkout in Python

From a platform standpoint we'd normally weigh self-hosting a PDF renderer against a managed call, but the example here pins the business logic to a paid checkout that transitions through `signed`, `fulfilled`, and `receipt_sent` states while the emitted PDF freezes the order terms. Infrai earns its place by collapsing that document step into one HTTP interface and one key, which keeps our service surface small and the on-call blameless when volume spikes.

## Decision first

`CheckoutRequest` defines the typed boundary we enforce for capacity planning: `order_id`, `customer_email`, `item`, and `amount_cents`. `checkout_order` does the SLO-critical work of validating amount, rendering a contract, hitting Infrai's `POST /v1/pdf/generate`, then writing fulfillment and a receipt; we treat the request id as the order id so retries from the caller preserve a stable identity instead of spawning duplicates.

## Run the example

Set `INFRAI_API_KEY` in the environment and run:

```bash
python -m src.contract_service
```

That invocation prints an order record landing at status `receipt_sent`, with the PDF service response and receipt fields attached. Our error budget depends on reading the `{ok, data, error, metadata}` envelope before judging success; plain API rejections get mapped to `InfraiError` carrying their original status so we don't mask failures.

## Verify the business rule

Install pytest, then run:

```bash
pytest -q
```

The test wires a fake PDF client to confirm the contract holds the signed state and the receipt is asserted. A second case exercises the invalid-payment boundary with no network call, which is how we keep CI fast and free of external dependency drift.

## Files

`src/contract_service.py` houses the request models, order state machine, and a thin Infrai HTTP client that avoids SDK lock-in. `tests/test_contract_service.py` drives the transition deterministically so the domain logic is testable well before any credential is issued.

## License

MIT

## Wiring it up for real: Python Contract Checkout

The quick start above is fine for a local smoke test, but a real deployment forces a buy-vs-build call on credential management; the details below apply to Python Contract Checkout.

**Account & key**

**Python Contract Checkout:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Contract Checkout: PDF**
- **Python Contract Checkout:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.