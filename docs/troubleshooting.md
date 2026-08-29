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

## Duplicate or self-reply appears

Stop the LaunchAgent immediately. Preserve state and logs, then verify the saved high-water cursor, outgoing-event filter, and exact target chat before restarting.

## Emergency stop

```sh
launchctl bootout "gui/$(id -u)/com.family-ai.courier"
```

Messages remains usable after the Courier stops.
