# Troubleshooting

## A setup command is not found

Follow the README's prerequisites first: Homebrew (including Command Line Tools and its PATH setup), Git, make, and `brew install python@3.11`. Use `python3.11`, not an unverified `python3`, for the walkthrough. Run commands from the downloaded project folder under the chatbot's macOS login.

## Codex reports that it is not logged in

Run `/Applications/ChatGPT.app/Contents/Resources/codex login`, finish the browser flow with the chosen ChatGPT account, then repeat the same command with `login status`. If Codex is installed elsewhere, use the path from the private configuration. Never paste account credentials into a chat.

## `imsg` cannot read Messages

Confirm Messages is signed in, then run:

```sh
imsg chats --limit 1 --json
```

If access is denied, grant Full Disk Access to the exact terminal or background process running the Courier. Restart the process after changing the permission.

## Reading works but sending fails

Send one harmless manual test with `imsg`. macOS should ask whether the controlling process may automate Messages. Review System Settings → Privacy & Security → Automation.

## Incoming text receives no reply

Check, in order:

1. The exact numeric chat ID is allowlisted.
2. The LaunchAgent is running.
3. The `imsg watch` process is producing rows.
4. `codex login status` succeeds for the same macOS user.
5. The configured Codex path is still valid after an app update.
6. The error log contains no stale Full Disk Access or Automation denial.
7. Replies were enabled before startup. For a fresh setup, stop the service and run `python3.11 courier.py enable-replies`, then restart. Configuration changes require a process restart.

## Enable replies reports a problem

Fix missing/invalid JSON, remaining placeholders, or nonnumeric chat IDs in the private configuration. The command also refuses unfinished or unreadable scheduled records; stop and review those without deleting history. See the configuration guide for deliberately resuming an existing scheduled queue. The command does not start the service or send anything.

## Optional: troubleshoot without sending

Stop the service and set `dry_run` to `true`, then run it in the foreground as described in the README. It still uses ChatGPT for conversational replies, but skips sending them and pauses scheduled delivery. No queued record is marked delivered or retried. A fresh installation does not need this extra stage before its supervised live test.

For a synthetic model-only check, use the README's optional `test-prompt` command. It prints the generated answer but does not send it.

Before turning live mode back on, review the scheduled outbox and restart the process. Overdue pending or retrying messages become eligible to send; conversations already processed in dry-run mode are not replayed.

## Duplicate or self-reply appears

Stop the LaunchAgent immediately. Preserve state and logs, then verify the saved high-water cursor, outgoing-event filter, and exact target chat before restarting.

## Emergency stop

```sh
launchctl bootout "gui/$(id -u)/com.family-ai.courier"
```

Messages remains usable after the Courier stops.

## A Python or ChatGPT update broke the LaunchAgent

The LaunchAgent pins the resolved Python path and the configuration pins the Codex path. From the repository checkout, re-run:

```sh
make check PYTHON=python3.11
./install.sh --activate
```

This refreshes the installed runtime and LaunchAgent while preserving configuration, state, and outbox data.

## Remove the Courier

```sh
./install.sh --uninstall
```

The command removes the LaunchAgent and installed runtime but preserves configuration, state, outbox, and logs for deliberate review or manual removal.
