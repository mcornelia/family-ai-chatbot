# Supervised Codex setup prompt

Use this prompt only after reading the repository's safety warning. Paste it into a Codex task running locally on the dedicated Mac. Stay present for permission prompts, enter account credentials yourself, and approve one supervised live test before enabling replies for the family.

Replace the bracketed values first. Do not paste phone numbers, Apple Account addresses, passwords, tokens, or private chat text into this prompt.

```text
Help me install and validate the public Family AI ChatBot repository on this dedicated Mac:
https://github.com/mcornelia/family-ai-chatbot

Act as a careful local administrator. Read README.md, SECURITY.md, and the docs before changing anything. Preserve existing files and configuration. Never print or commit phone numbers, Apple Account addresses, chat IDs, credentials, private Messages content, or generated replies.

My desired public labels are:
- assistant name: [ASSISTANT NAME]
- administrator label: [GENERIC ADMINISTRATOR LABEL]
- approved chat labels: [CHAT LABELS ONLY — NO ADDRESSES OR IDS]

Follow this sequence:
1. Verify macOS, Homebrew, Git, make, Python 3.11+, imsg, Messages sign-in, and the bundled Codex CLI. Help me install missing prerequisites with appropriate administrator approval, while keeping Courier setup under the chatbot's macOS login. Explain any missing permission and let me approve it in macOS myself. Run the configured Codex CLI's login status; if signed out, guide me through its browser login and recheck for ChatGPT authentication.
2. Run make check PYTHON=python3.11 before installation, using the same supported interpreter for the later foreground service. If deliberately using another supported version, use it consistently. Stop and report any failure.
3. Run ./install.sh without activation.
4. Ask before accessing real Messages data. Help me obtain numeric chat row IDs locally with imsg. Do not echo private handles or IDs back into chat. Have me edit the private config file directly.
5. Begin with only the private chat between my phone and the bot. Remove unused example contacts, replace every REPLACE_ placeholder, and keep history_limit bounded. Confirm no other Courier instance is running and the scheduled outbox is empty. If an existing installation has pending messages, stop and help me review them without deleting its history. Quiet hours and mention-only mode are not included in this reference implementation.
6. Explain that the test will send context to ChatGPT and a real reply to that one chat. Pause for my explicit approval before running python3.11 courier.py enable-replies and starting the foreground service. The enable-replies command only updates the configuration; stop if it reports a problem. Do not start the foreground service until it succeeds.
7. Once the service reports that it is ready, ask me to send one harmless incoming message. Verify exactly one reply in the same chat and no self-reply loop. Stop the foreground process and confirm it exited. If anything fails, troubleshoot without broadening the chat allowlist.
8. After that test passes, ask for separate approval to add consented family chats and run ./install.sh --activate. Do not run the background service alongside the foreground process.
9. Verify one reply in the direct chat and one consented group chat. Restart the Mac, sign back into the dedicated account, and check that old messages are not replayed. Test the emergency stop.
10. Show me the status, emergency-stop, update, uninstall, and outbox-retention commands. Summarize what changed without revealing private identifiers.

Use ChatGPT subscription authentication as the default. Do not create or request an OpenAI API key unless I explicitly choose that advanced alternative after reviewing its billing and credential implications.

If I choose optional dry-run troubleshooting, explain that it still uses ChatGPT but blocks conversational sends and pauses the scheduled outbox. Restart after changing modes, and review overdue queued messages before resuming live delivery.
```

This prompt guides a supervised installation; it is not a script and does not grant permission to bypass macOS consent dialogs or activate sending without approval.
