# Immutable Ledger (`apps/ledger`)

## Purpose
Records every financial movement as an immutable, balanced, double-entry
transaction. Wallet balances are a cached projection of these entries.

## Module contract
- **Inputs:** signed `(WalletAccount, amount)` entry pairs from services.
- **Outputs:** `LedgerTransaction` + immutable `LedgerEntry` rows; updated
  cached balances.
- **Dependencies:** `apps/wallets` (accounts).
- **Events emitted:** none (callers emit business events).
- **Events consumed:** none.
- **Database tables:** `LedgerTransaction`, `LedgerEntry`.
- **Public APIs:** internal Python service only.
- **Security requirements:** services-only; no direct balance writes.

## Business rules
- Entries must sum to zero (`post_transaction` raises otherwise).
- Entries are immutable; corrections are `REVERSAL` transactions.
- `idempotency_key` is unique; replays return the existing transaction.
- Balance changes use `select_for_update()` inside one atomic block.
- Money is `NUMERIC(20,8)` / `Decimal` only.

## Key functions
- `post_transaction(type, entries, reference, description, metadata,
  idempotency_key, status) -> (txn, created)`
- `reverse_transaction(txn, reason) -> (reversal, created)`
- `account_balance(account) -> Decimal` (ledger truth)
- `verify_account_balance(account) -> bool` (cache vs ledger)

## Tests
`pytest tests/test_critical_flows.py -q` (balance, idempotency, immutability,
reversal).
