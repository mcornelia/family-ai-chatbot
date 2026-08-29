# Family AI ChatBot

A small, local-first iMessage bridge for a household AI running on a dedicated Mac.

Family AI Courier watches only explicitly allowlisted Messages chats, sends a bounded slice of recent context to an ephemeral Codex CLI run, and returns one short reply to the same chat. It uses the Mac's existing Messages identity and an authenticated Codex CLI—no OpenClaw service and no custom OpenAI API integration are required.

> **Read this first:** this software can read private conversations and send messages automatically. Use a dedicated Mac account, obtain consent from every participant, start in `dry_run` mode, and keep an immediate stop procedure available. It is not an emergency, medical, legal, or financial system.

The longer design story is in [Build a Family AI ChatBot](https://mcornelia.com/posts/family-ai-chatbot.html).

## What it does

- Starts one event-driven `imsg watch` stream for every allowlisted direct or group chat.
- Baselines existing history on first launch, so old messages are not answered.
- Ignores outgoing events to prevent self-reply loops.
- Loads at most the configured number of recent messages from the triggering chat only.
- Labels group speakers using an explicit handle-to-name map.
- Invokes `codex exec` ephemerally in an empty directory with a read-only sandbox.
- Gives the automatic model turn no tools and instructs it not to claim outside actions.
- Sends one short reply back to the same numeric chat ID.
- Includes a persistent, duplicate-checked scheduled outbox.
- Runs as a per-user macOS LaunchAgent and restarts after login or failure.

See [Architecture](docs/architecture.md) for trust boundaries and delivery semantics.

## Requirements

- macOS 14 or newer with Messages signed in.
- Python 3.11 or newer. The Courier uses only the Python standard library.
- [`imsg`](https://imsg.sh/), with Full Disk Access for reading Messages and Automation permission for sending.
- ChatGPT for macOS or another installed Codex CLI, authenticated with either ChatGPT subscription access or an OpenAI API key.

The default configuration points to the Codex executable bundled with ChatGPT for macOS:

```text
/Applications/ChatGPT.app/Contents/Resources/codex
```

## Quick start

### 1. Install and verify `imsg`

```sh
brew install steipete/tap/imsg
imsg --version
imsg chats --limit 3
```

Follow the [`imsg` permissions guide](https://imsg.sh/quickstart.html) before continuing. Do not enable its optional private-framework features or disable System Integrity Protection for this project.

### 2. Authenticate Codex

Install ChatGPT for macOS, sign in, and verify the bundled CLI:

```sh
/Applications/ChatGPT.app/Contents/Resources/codex login status
```

Codex supports ChatGPT subscription sign-in and API-key sign-in. See the official [OpenAI authentication guide](https://learn.chatgpt.com/docs/auth).

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

Then edit:

```text
~/Library/Application Support/Family AI Courier/config.json
```

Replace every `REPLACE_...` placeholder. For a group chat, map each exact sender handle to a friendly label. Keep `dry_run` set to `true`. See [Configuration](docs/configuration.md) for every field.

Never commit the real configuration. It contains private chat identifiers even if it contains no password.

### 5. Test without sending

Generate a synthetic reply through Codex:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  test-prompt Alex "Hello from the setup test"
```

Then run the Courier in the foreground with `dry_run: true`, send one harmless incoming test message, and inspect the generated reply:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  --state "$HOME/Library/Application Support/Family AI Courier/state.json"
```

Stop it with Control-C.

### 6. Activate carefully

After the chat IDs and dry-run output are correct, change `dry_run` to `false`, then:

```sh
./install.sh --activate
```

Send one harmless message in one approved direct chat. Confirm exactly one reply appears in the same chat. Repeat once in a consented group chat, then restart the Mac and verify that old messages are not replayed.

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

Queue a duplicate-safe scheduled message:

```sh
python3 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  queue-message "Family Group" \
  --send-at "2026-09-01T08:00:00-04:00" \
  --text "Good morning!"
```

List outbox state without printing message text:

```sh
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

See [Troubleshooting](docs/troubleshooting.md) for permission, login, and loop checks.

## Privacy model

- Chat text is read from the local Messages database through `imsg`.
- Only allowlisted chat IDs are watched.
- Only bounded recent context from the triggering chat is placed in the model prompt.
- That prompt is sent to the OpenAI service associated with the Codex sign-in. Review the applicable workspace and data controls before use.
- Full message transcripts are not intentionally written to Courier logs. Scheduled-message text is stored in the private outbox until its record is removed.
- Attachments are not sent to the model or interpreted by this release.

Read [SECURITY.md](SECURITY.md) before enabling automatic sending.

## Tests

```sh
make check
```

The suite is synthetic: it mocks `imsg` and Codex and never opens Messages or sends a message.

## Project status and license

This is a reference implementation extracted from a working household deployment. macOS, Messages, Codex CLI, and `imsg` behavior can change; re-test after significant updates.

No open-source license has been selected yet. Public availability does not itself grant permission to copy, modify, or redistribute the code beyond rights provided by applicable law and GitHub's terms. A license can be added deliberately later.
