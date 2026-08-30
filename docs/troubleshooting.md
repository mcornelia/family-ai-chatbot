# Troubleshooting

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
7. `dry_run` is `false` if you expect a real reply. Configuration changes require a process restart.

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
make check
./install.sh --activate
```

This refreshes the installed runtime and LaunchAgent while preserving configuration, state, and outbox data.

## Remove the Courier

```sh
./install.sh --uninstall
```

The command removes the LaunchAgent and installed runtime but preserves configuration, state, outbox, and logs for deliberate review or manual removal.
