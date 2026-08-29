# Configuration reference

The default configuration path is:

```text
~/Library/Application Support/Family AI Courier/config.json
```

| Field | Purpose |
| --- | --- |
| `assistant_name` | Name used in the model prompt and attachment acknowledgement. |
| `assistant_description` | Short tone and role description. Do not put secrets here. |
| `owner_name` | Person or role the sender is asked to contact directly for consequential requests. The Courier does not notify this person separately. |
| `host_description` | Generic description of the dedicated Mac. Avoid an address or family surname. |
| `signature_mark` | Optional occasional emoji; use an empty string to disable it. |
| `personas` | Optional owner-controlled map of exact `@selector` keys to personality definitions. Keys are case-insensitive and may contain letters, numbers, `_`, or `-`. `help` is reserved. |
| `personas[].display_name` | Label used in the prompt, `@help`, and—by default—the outgoing reply. |
| `personas[].description` | Trusted tone and specialty instructions. A persona cannot change the shared safety rules or permissions. |
| `personas[].label_replies` | Optional boolean; defaults to `true`. When enabled, the Courier prepends `Display Name:` to replies from that persona. |
| `personas[].signature_mark` | Optional per-persona replacement for the default occasional emoji. |
| `default_persona` | Optional configured persona key used when a message has no selector. |
| `contacts` | Exact allowlist of direct or group chats. |
| `contacts[].chat_id` | Numeric row ID returned by `imsg chats --json`. |
| `contacts[].relationship` | Brief context supplied to the model. |
| `contacts[].participants` | For a group, map exact sender handles to display labels. |
| `contacts[].default_persona` | Optional per-chat default that overrides the global `default_persona`. |
| `history_limit` | Recent messages loaded from the triggering chat; accepted range is 1–50. |
| `imsg_path` | Absolute path to the `imsg` executable. |
| `codex_path` | Absolute path to an authenticated Codex CLI. |
| `codex_model` | Optional model override. Leave empty to use the current Codex default. |
| `codex_thinking` | Optional Codex reasoning-effort setting. |
| `outbox_check_interval_seconds` | Local scheduled-outbox check interval. No model request occurs while idle. |
| `outbox_duplicate_window_seconds` | Look-back window used to find a recent identical outgoing scheduled message; accepted range is 60–86,400 seconds. The default is 900 seconds. |
| `dry_run` | When true, generates a reply without sending it. The body is not logged by default. |
| `log_dry_run_reply` | Optional boolean, default `false`. Setting it to `true` writes model-generated reply text to logs and may expose private conversation-derived content. |

Keep personal configuration outside the repository. The installer creates it with mode `0600`, and `.gitignore` excludes common local configuration filenames.

## Optional `@persona` routing

When `personas` is configured, a participant can put one exact selector at the start of a message:

```text
@Sage Help us think through a household decision
@Spark Make this invitation more fun
@help
```

The Courier removes a recognized selector before building the model prompt. `@help`, an unknown selector, a selector with no message, or multiple selectors receives a deterministic local response without a model call. A selector changes only the trusted personality description; every persona inherits the same chat allowlist, bounded same-chat context, isolated Codex process, direct-contact handoffs, and emergency stop.

If `personas` is omitted, leading `@names` are treated as ordinary message text. This keeps the feature opt-in and avoids intercepting normal conversation.

## Features not included

This reference implementation does not include quiet hours or mention-only activation. Add those policies explicitly, document the behavior for participants, and test them before relying on them. A personality selector is not a permission boundary and does not make a chat mention-only.

## Scheduled-message retention

Scheduled text is stored in owner-readable JSON files. `list-outbox` never prints that text. Preview old terminal records before deleting them:

```sh
python3 courier.py --config "/path/to/config.json" purge-outbox --older-than-days 30
```

Run the same command with `--confirm` to delete matching **delivered** and **canceled** records. Pending or retrying messages are never selected. Cleanup is manual rather than automatic so an operator can retain the audit history that fits the household's policy.
