# Configuration reference

The default configuration path is:

```text
~/Library/Application Support/Family AI Courier/config.json
```

| Field | Purpose |
| --- | --- |
| `assistant_name` | Name used in the model prompt and attachment acknowledgement. |
| `assistant_description` | Short tone and role description. Do not put secrets here. |
| `owner_name` | Person or role to whom consequential requests are handed off. |
| `host_description` | Generic description of the dedicated Mac. Avoid an address or family surname. |
| `signature_mark` | Optional occasional emoji; use an empty string to disable it. |
| `contacts` | Exact allowlist of direct or group chats. |
| `contacts[].chat_id` | Numeric row ID returned by `imsg chats --json`. |
| `contacts[].relationship` | Brief context supplied to the model. |
| `contacts[].participants` | For a group, map exact sender handles to display labels. |
| `history_limit` | Recent messages loaded from the triggering chat; accepted range is 1–50. |
| `imsg_path` | Absolute path to the `imsg` executable. |
| `codex_path` | Absolute path to an authenticated Codex CLI. |
| `codex_model` | Optional model override. Leave empty to use the current Codex default. |
| `codex_thinking` | Optional Codex reasoning-effort setting. |
| `outbox_check_interval_seconds` | Local scheduled-outbox check interval. No model request occurs while idle. |
| `dry_run` | When true, generates and logs a reply without sending it. |

Keep personal configuration outside the repository. The installer creates it with mode `0600`, and `.gitignore` excludes common local configuration filenames.
