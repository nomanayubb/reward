# PROJECT GOAL

## Product

Build a production-grade rewards platform using Python/Django.

The platform combines:

- HTML5 games
- surveys
- compliant CPA/offerwall integrations
- app/task offers where incentivization is permitted
- advertising
- referrals
- bonuses
- user wallets
- points
- cash rewards
- deposits
- withdrawals
- crypto payments
- Pakistani payment methods
- fraud prevention
- KYC where required
- analytics
- highly configurable administration

## Core Principle

The platform must be modular, secure, scalable, maintainable, fast, and highly
configurable. Business rules should be configurable from the admin panel
whenever practical instead of being hard-coded.

## Financial Principle

All financial activity must use an immutable ledger. Never directly modify
balances without creating the appropriate ledger transaction. All external
conversions and payment callbacks must be idempotent.

## Provider Principle

External providers must use adapters/interfaces. Provider-specific code must
not be scattered throughout the project.

## Game Principle

HTML5 games must remain isolated from the main application. Each game has its
own folder and documentation.

## AI Development Principle

The project must be developed incrementally.

Before changing code:

1. Read RULES.md
2. Read STATE.md
3. Read TASKS.md
4. Read relevant module documentation
5. Inspect the existing implementation
6. Make the smallest coherent change
7. Run appropriate tests
8. Update project state/documentation
9. Commit the change
10. Push to Git

Never blindly rewrite existing working code.

## Success Definition

A user can register, play a game, complete a survey and an offer, receive a
provider conversion, get a pending reward, see it approved into the wallet,
request a withdrawal, have it processed by an admin, and the payment can be
reconciled — with every financial movement recorded in the immutable ledger.
