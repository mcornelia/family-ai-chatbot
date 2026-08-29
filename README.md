# Family AI ChatBot

A small, local-first iMessage bridge for a household AI running on a dedicated Mac.

**Family AI Courier** is the custom Python service in this repository. It watches only explicitly allowlisted Messages chats, sends a bounded slice of recent context to an ephemeral Codex CLI run, and returns one short reply to the same chat. It uses the Mac's existing Messages identity and an authenticated Codex CLI—no OpenClaw service or custom OpenAI API integration is required.

> **Read this first:** this software can read private conversations and send messages automatically. Use a dedicated Mac account, obtain consent from every participant, start in `dry_run` mode, and keep an immediate stop procedure available. It is not an emergency, medical, legal, or financial system.

The longer design story is in [Build a Family AI ChatBot](https://mcornelia.com/posts/family-ai-chatbot.html). If you already use Codex, the [copy/paste setup prompt](docs/setup-prompt.md) can guide a supervised installation.

## What it does

- Starts one event-driven `imsg watch` stream for every allowlisted direct or group chat.
- Baselines existing history on first launch, so old messages are not answered.
- Ignores outgoing events to prevent self-reply loops.
- Loads the configured 1–50 recent messages from the triggering chat only.
- Labels group speakers using an explicit handle-to-name map.
- Optionally routes an exact leading selector such as `@Sage` or `@Spark` to an owner-configured personality without changing permissions or chat scope.
- Runs `codex exec` ephemerally in an empty temporary directory, with a read-only sandbox and user configuration disabled. Its prompt instructs Codex not to use tools or take outside actions.
- Sends one short reply back to the same numeric chat ID.
- Includes a persistent scheduled outbox with bounded duplicate checking and explicit retention cleanup.
- Runs as a per-user macOS LaunchAgent and restarts after login or failure.

See [Architecture](docs/architecture.md) for trust boundaries, limitations, and delivery semantics.

## Requirements

- macOS 14 or newer with Messages signed in.
- Python 3.11 or newer. The Courier uses only the Python standard library.
- [`imsg`](https://imsg.sh/), with Full Disk Access for reading Messages and Automation permission for sending.
- ChatGPT for macOS or another installed Codex CLI, signed in with a ChatGPT subscription.

The default Codex path is:

```text
/Applications/ChatGPT.app/Contents/Resources/codex
```

API-key authentication is possible, but it changes the billing, credential-management, and data-control assumptions in this guide. Treat it as an advanced alternative and review the official [OpenAI authentication guide](https://learn.chatgpt.com/docs/auth) first.

## Quick start

### 1. Install and verify `imsg`

```sh
brew install steipete/tap/imsg
imsg --version
imsg chats --limit 3
```

Follow the [`imsg` permissions guide](https://imsg.sh/quickstart.html). Do not enable optional private-framework features or disable System Integrity Protection for this project.

### 2. Authenticate Codex

Install ChatGPT for macOS, sign in with the household's dedicated ChatGPT account, and verify its bundled CLI:

```sh
/Applications/ChatGPT.app/Contents/Resources/codex login status
```

### 3. Clone, test, and install

```sh
git clone https://github.com/mcornelia/family-ai-chatbot.git
cd family-ai-chatbot
make check
./install.sh
```

The installer copies the runtime to `~/Applications/family-ai-chatbot`, creates private support directories, installs a LaunchAgent definition, and leaves the service stopped.

### 4. Configure the allowlist

Inspect chat IDs locally:

```sh
imsg chats --limit 20 --json
```

Edit:

```text
~/Library/Application Support/Family AI Courier/config.json
```

Replace every `REPLACE_...` placeholder. Map exact sender handles to friendly labels for a group chat, and keep `dry_run` set to `true`. See [Configuration](docs/configuration.md) for every field.

Never commit the real configuration. It contains private chat identifiers even if it contains no password.

### 5. Test without sending

Generate a synthetic reply through Codex:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  test-prompt Alex "Hello from the setup test"
```

Then run the Courier in the foreground, send one harmless incoming test message, and confirm that the log records a generated reply without printing its body:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  --state "$HOME/Library/Application Support/Family AI Courier/state.json"
```

Stop it with Control-C.

### 6. Activate and verify

After the chat IDs and dry-run behavior are correct, change `dry_run` to `false`, then:

```sh
./install.sh --activate
```

Send one harmless message in one approved direct chat and confirm exactly one reply appears there. Repeat once in a consented group chat, restart the Mac, and verify that old messages are not replayed.

A successful private dry run looks like this—the generated text itself is intentionally absent:

```text
INFO Incoming row 123 from Alex (18 chars)
INFO DRY RUN generated a 96-character reply to Alex; body not logged
```

## Optional personalities

The example configuration includes `Sage` and `Spark`. A participant can begin a message with `@Sage`, `@Spark`, or `@help`. Selection is exact and case-insensitive. Unknown, empty, or multiple selectors receive a local help response without invoking Codex.

Personas change only the trusted display name, tone description, optional signature mark, and reply label. They retain the same allowlist, context limit, isolated Codex process, safety rules, and direct-contact handoffs. See [Configuration](docs/configuration.md#optional-persona-routing).

Quiet hours and mention-only activation are **not implemented** in this reference release. Add and test those policies locally before promising them to participants.

## Operations

Status:

```sh
launchctl print "gui/$(id -u)/com.family-ai.courier"
```

Emergency stop:

```sh
launchctl bootout "gui/$(id -u)/com.family-ai.courier"
```

Logs:

```sh
tail -f "$HOME/Library/Logs/Family AI Courier/courier.log"
```

Queue and inspect a scheduled message:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  queue-message "Family Group" \
  --send-at "2026-09-01T08:00:00-04:00" \
  --text "Good morning!"

python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  list-outbox
```

Cancel a pending item:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  cancel-message MESSAGE_ID
```

Preview and then delete delivered or canceled outbox records older than 30 days:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  purge-outbox --older-than-days 30

python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  purge-outbox --older-than-days 30 --confirm
```

The preview and list commands show IDs and metadata, never message text.

### Update

The installed runtime is a copy; `git pull` alone does not update it. Re-test and reinstall deliberately:

```sh
git pull --ff-only
make check
./install.sh --activate
```

The installer preserves the existing private configuration, state, and outbox. Re-check the configured Python and Codex paths after Homebrew, Python, or ChatGPT upgrades.

### Uninstall

```sh
./install.sh --uninstall
```

This stops the LaunchAgent and removes the installed runtime and LaunchAgent file. It deliberately preserves configuration, state, outbox, and logs under `~/Library`; review and remove those separately if you no longer need them.

See [Troubleshooting](docs/troubleshooting.md) for permission, login, and loop checks.

## Privacy and operational limits

- Chat text is read locally through `imsg`, but the bounded prompt is sent to the OpenAI service associated with the Codex sign-in.
- The prompt tells Codex not to use tools or take outside actions; the process is also ephemeral, isolated in an empty directory, read-only, and launched without user configuration. This is defense in depth, not a claim that the CLI has a hard zero-tool mode.
- Full message transcripts and generated dry-run replies are not logged by default. Setting `log_dry_run_reply` to `true` intentionally weakens that protection.
- Scheduled-message text remains in private outbox JSON until purged.
- Attachments are not sent to the model or interpreted. The reply asks the sender to contact the configured administrator directly; the Courier does not notify that person separately.
- Incoming events from all chats share one reply-processing queue. A slow Codex call can delay another chat by up to the configured process timeout.
- Automatic conversational replies are at most once: a transient failure can result in no reply rather than a duplicate reply.

Read [SECURITY.md](SECURITY.md) before enabling automatic sending.

## Tests

```sh
make check
```

The suite is synthetic: it mocks `imsg` and Codex and never opens Messages or sends a message. GitHub Actions runs it on Python 3.11, 3.12, and 3.13. There is no automated macOS Messages integration test, so repeat the harmless manual checks after significant OS, ChatGPT, `imsg`, or Python updates.

## Project status and license

This is a reference implementation extracted from a working household deployment. See [CHANGELOG.md](CHANGELOG.md) for release history.

Licensed under the [MIT License](LICENSE).
