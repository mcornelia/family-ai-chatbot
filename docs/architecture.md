# Architecture

```text
Approved iMessage chat
        │ incoming event
        ▼
`imsg watch` ── outgoing or old row ──► ignore
        │
        ▼
Family AI Courier (local Python service)
        │ bounded same-chat context
        ▼
ephemeral `codex exec` in an empty, read-only sandbox
        │ one short text reply
        ▼
Family AI Courier ── `imsg send` ──► same numeric chat ID
```

The Courier also checks a local persistent outbox for scheduled messages. Before each scheduled send it looks for an identical outgoing copy only within a configurable recent time window (15 minutes by default), so an old recurring greeting does not suppress a legitimate new one. A successful `imsg send` is the delivery commit boundary; a temporarily lagging history read cannot trigger a duplicate retry.

## Trust boundaries

- Only numeric chat IDs in `config.json` are watched.
- Context is limited to the configured number of recent messages from the triggering chat.
- Incoming text is treated as untrusted conversation content, not as an instruction to change system rules.
- The automatic prompt instructs Codex not to use tools or take outside actions. The CLI process is ephemeral, starts in an empty temporary directory with a read-only sandbox, and ignores user configuration. These are layered constraints, not a hard claim that the Codex CLI exposes no tools.
- Optional exact `@persona` routing selects only an owner-configured display name and tone description. It cannot widen the allowlist, context, process restrictions, permissions, or safety policy; invalid selectors are handled locally without a model call.
- Attachments are not interpreted. The Courier asks the sender to contact the configured administrator directly; it does not send a separate alert.
- Configuration and saved cursors live outside the source checkout under the user's Library folder.

## Delivery semantics

Automatic conversational replies are intentionally **at most once**. The saved high-water cursor advances before model generation and sending. This prevents a crash or restart from replaying an old incoming message, but a transient model or send failure can mean that message receives no automatic reply. The error is logged for human review.

Scheduled outbox delivery has different semantics: pending failures are retained with bounded backoff, duplicate-checked before sending, and marked delivered after a successful send command.

With `dry_run: true`, conversational reply generation still runs but the send is skipped and the incoming-message cursor advances. Scheduled delivery is paused before any Messages lookup or delivery-state update; pending and retrying records remain untouched. After restarting with `dry_run: false`, overdue scheduled entries become eligible again, while conversational events already handled in dry-run mode are not replayed.

## Concurrency and retention

Each allowlisted chat has its own watcher, but incoming events share one reply-processing queue. This preserves simple ordering and is suitable for a small household; one slow Codex request can temporarily delay every chat for up to the model-process timeout.

Delivered and canceled outbox records retain their message text until the operator runs `purge-outbox --confirm`. Cleanup is deliberately explicit. Pending and retrying records are never purged by that command.
