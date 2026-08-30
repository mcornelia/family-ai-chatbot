# Family AI ChatBot

A small, local-first iMessage bridge for a household AI running on a dedicated Mac.

**Family AI Courier** is the custom Python service in this repository. It watches only explicitly allowlisted Messages chats, sends a bounded slice of recent context to an ephemeral Codex CLI run, and returns one short reply to the same chat. It uses the Mac's existing Messages identity and an authenticated Codex CLI—no OpenClaw service or custom OpenAI API integration is required.

> **Read this first:** this software can read private conversations and send messages automatically. Use a dedicated Mac account, obtain consent from every participant, start with one supervised live test in your own private chat with the bot, and keep a stop procedure available. It is not an emergency, medical, legal, or financial system.

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

### 0. Check the command-line tools

Run setup from the chatbot's dedicated macOS login, not as root. On a fresh Mac, follow the [Homebrew installation guide](https://docs.brew.sh/Installation), including the Xcode Command Line Tools and the installer's PATH instructions. Have the Mac's administrator help with that one-time installation if needed.

Check the tools before continuing:

```sh
brew --version && git --version && make --version
```

Install the [Python version used by this walkthrough](https://formulae.brew.sh/formula/python@3.11) and check it:

```sh
brew install python@3.11 && python3.11 --version
```

Use `python3.11` in the commands below. Plain `python3` can still point to Apple's older Python even after a newer version is installed. Stop and fix any failed prerequisite before proceeding. Other Python versions supported by the project can be used deliberately, but keep the interpreter consistent across tests, foreground runs, and installation.

### 1. Install and verify `imsg`

```sh
brew install steipete/tap/imsg &&
imsg --version &&
imsg chats --limit 3
```

Follow the [`imsg` permissions guide](https://imsg.sh/quickstart.html). Do not enable optional private-framework features or disable System Integrity Protection for this project.

### 2. Authenticate Codex

Install ChatGPT for macOS, sign in with the household's dedicated ChatGPT account, and verify its bundled CLI:

```sh
/Applications/ChatGPT.app/Contents/Resources/codex login status
```

If it reports that you are not logged in, run:

```sh
/Applications/ChatGPT.app/Contents/Resources/codex login
```

Complete the browser sign-in using the chatbot's chosen ChatGPT account, then repeat `login status`. This is the [documented CLI sign-in flow](https://learn.chatgpt.com/docs/auth#sign-in-with-chatgpt). Do not proceed until it reports ChatGPT authentication.

### 3. Clone, test, and install

```sh
git clone https://github.com/mcornelia/family-ai-chatbot.git &&
cd family-ai-chatbot &&
make check PYTHON=python3.11 &&
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

Replace every `REPLACE_...` placeholder and begin with **only one contact entry**: the private chat between your phone and the bot. Remove the other example contact entries; add family and group chats after this test passes. See [Configuration](docs/configuration.md) for every field.

Never commit the real configuration. It contains private chat identifiers even if it contains no password.

### 5. Try one live conversation

Before starting, confirm no other Courier process or LaunchAgent is running and the scheduled outbox is empty (`list-outbox` in [Operations](#operations) shows its contents). If this is an existing installation, stop it and review its pending messages first; do not delete configuration or delivery history just to test.

From the downloaded `family-ai-chatbot` folder, **enable replies** when you are ready:

```sh
python3.11 courier.py enable-replies
```

This updates only the sending setting in the private configuration. It does not start the service, read Messages, call ChatGPT, or send anything. It refuses incomplete configurations or unfinished/unreadable scheduled messages; fix those before continuing. Existing settings, conversation state, and scheduled records are preserved. Repeating the command is harmless. The command prepares the next start; it does not reconfigure a running process.

Run the Courier in the foreground—leave this Terminal window open so you can watch it:

```sh
python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  --state "$HOME/Library/Application Support/Family AI Courier/state.json"
```

Once it reports that it is ready, send one harmless message from your phone to the bot. Confirm exactly one reply appears in that private chat and the bot does not answer itself. Stop it with Control-C and wait for the process to exit. If the reply is missing or duplicated, stop and troubleshoot before adding anyone else.

### 6. Activate and verify

With the foreground process stopped, add only consented family chats to the configuration and map exact sender handles to friendly labels for group chats. Then enable background operation:

```sh
./install.sh --activate
```

Repeat one harmless test in the direct chat and one consented group chat. Restart the Mac, sign back into the dedicated account, and verify that old messages are not replayed. Test the emergency stop before leaving the service unattended.

### Optional: diagnose without sending

Use this only if you want to inspect the reply-generation path without texting anyone. Stop the running service, set `dry_run` to `true`, and run the foreground command from step 5. Incoming conversations still supply bounded context to ChatGPT and use your account's limits, but no conversational replies are sent. Scheduled delivery is paused without changing queued records. Generated reply bodies stay out of logs unless you explicitly enable `log_dry_run_reply`.

To test only the model connection with synthetic text, use this optional command instead. Replace `Your test chat label` with the configured contact's `name`; this command prints the generated answer but never sends it:

```sh
python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  test-prompt "Your test chat label" "Hello from the setup test"
```

Stop the process before changing modes. Before setting `dry_run` back to `false` and restarting, review pending or retrying scheduled messages: anything overdue becomes eligible to send. Incoming messages already processed during dry-run mode are not replayed. A custom rewrite should also verify its no-send behavior in automated tests before a supervised live test.

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
python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  queue-message "Family Group" \
  --send-at "2026-09-01T08:00:00-04:00" \
  --text "Good morning!"

python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  list-outbox
```

Cancel a pending item:

```sh
python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  cancel-message MESSAGE_ID
```

Preview and then delete delivered or canceled outbox records older than 30 days:

```sh
python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  purge-outbox --older-than-days 30

python3.11 courier.py \
  --config "$HOME/Library/Application Support/Family AI Courier/config.json" \
  purge-outbox --older-than-days 30 --confirm
```

The preview and list commands show IDs and metadata, never message text.

### Update

The installed runtime is a copy; `git pull` alone does not update it. Re-test and reinstall deliberately:

```sh
git pull --ff-only
make check PYTHON=python3.11
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
make check PYTHON=python3.11
```

The suite is synthetic: it mocks `imsg` and Codex and never opens Messages or sends a message. GitHub Actions runs it on Python 3.11, 3.12, and 3.13. There is no automated macOS Messages integration test, so repeat the harmless manual checks after significant OS, ChatGPT, `imsg`, or Python updates.

## Project status and license

This is a reference implementation extracted from a working household deployment. See [CHANGELOG.md](CHANGELOG.md) for release history.

Licensed under the [MIT License](LICENSE).
