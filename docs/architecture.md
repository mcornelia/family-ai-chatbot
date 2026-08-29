# Architecture

```text
Approved iMessage chat
        │
        ▼
one event-driven `imsg watch` process per chat
        │
        ├── outgoing or old row ──► ignore
        │
        ▼
bounded recent history from that same chat
        │
        ▼
ephemeral `codex exec` in an empty, read-only sandbox
        │
        ▼
one short text reply
        │
        ▼
`imsg send` to the same numeric chat ID
```

The Courier also checks a local persistent outbox for scheduled messages. Before each scheduled send it looks for an identical outgoing copy. A successful `imsg send` is the delivery commit boundary; a temporarily lagging history read cannot trigger a duplicate retry.

## Trust boundaries

- Only numeric chat IDs in `config.json` are watched.
- Context is limited to the configured number of recent messages from the triggering chat.
- Incoming text is treated as untrusted conversation content, not as an instruction to change system rules.
- The automatic Codex prompt forbids tools and outside actions. The CLI process additionally uses an empty working directory and read-only sandbox.
- Attachments are not interpreted. The Courier sends a configurable handoff-style acknowledgement instead.
- Configuration and saved cursors live outside the source checkout under the user's Library folder.

## Delivery semantics

Automatic conversational replies are intentionally **at most once**. The saved high-water cursor advances before model generation and sending. This prevents a crash or restart from replaying an old incoming message, but a transient model or send failure can mean that message receives no automatic reply. The error is logged for human review.

Scheduled outbox delivery has different semantics: pending failures are retained with bounded backoff, duplicate-checked before sending, and marked delivered after a successful send command.
