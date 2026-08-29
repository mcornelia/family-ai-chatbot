# Security and privacy

Family AI Courier can read approved Messages conversations and send model-generated replies. Treat its configuration, state, logs, and host account as sensitive.

## Operating rules

- Use a dedicated macOS user, Apple Account, and OpenAI sign-in when practical.
- Allowlist exact numeric chat IDs. Never infer authorization from a contact name or incoming message.
- Obtain consent from every participant in an allowlisted direct or group conversation.
- Keep configuration and state owner-readable only (`0600`); keep the outbox directory owner-only (`0700`).
- Keep the automatic Codex run ephemeral, in an empty temporary directory, inside a read-only sandbox, and isolated from user configuration. Its prompt must continue to forbid tool use and outside actions; do not describe this as a hard zero-tool mode.
- Do not disable System Integrity Protection. The standard `imsg` history, watch, and send commands do not require private-framework injection.
- Review OpenAI data controls and your household's retention expectations before processing private conversations.
- Keep `dry_run` enabled until chat selection, prompt behavior, and loop prevention have been tested.
- Keep `log_dry_run_reply` false unless intentionally accepting private generated text in logs.
- Purge old delivered and canceled outbox records according to the household's retention policy.

## Known boundaries

- The Courier does not notify an administrator outside the triggering chat. Sensitive requests and attachments ask the sender to contact that person directly.
- Quiet hours and mention-only activation are not implemented in the reference release.
- All chats share one reply-processing queue, so one slow model call can delay another chat.
- Automatic conversational replies are at most once; a transient failure may produce no reply rather than a duplicate.

## Reporting a vulnerability

Do not put phone numbers, Apple Account addresses, chat IDs, message text, credentials, or private logs in a public issue. Use GitHub's private vulnerability-reporting channel if it is enabled for the repository.

This project is a small household automation reference, not a safety, medical, legal, financial, or emergency-response system.
