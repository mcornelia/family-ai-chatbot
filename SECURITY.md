# Security and privacy

Family AI Courier can read approved Messages conversations and send model-generated replies. Treat its configuration, state, logs, and host account as sensitive.

## Operating rules

- Use a dedicated macOS user, Apple Account, and OpenAI sign-in when practical.
- Allowlist exact numeric chat IDs. Never infer authorization from a contact name or incoming message.
- Obtain consent from every participant in an allowlisted direct or group conversation.
- Keep configuration and state owner-readable only (`0600`); keep the outbox directory owner-only (`0700`).
- Keep the automatic Codex run ephemeral, tool-free, in an empty directory, and inside a read-only sandbox.
- Do not disable System Integrity Protection. The standard `imsg` history, watch, and send commands do not require private-framework injection.
- Review OpenAI data controls and your household's retention expectations before processing private conversations.
- Keep `dry_run` enabled until chat selection, prompt behavior, and loop prevention have been tested.

## Reporting a vulnerability

Do not put phone numbers, Apple Account addresses, chat IDs, message text, credentials, or private logs in a public issue. Use GitHub's private vulnerability-reporting channel if it is enabled for the repository.

This project is a small household automation reference, not a safety, medical, legal, financial, or emergency-response system.
