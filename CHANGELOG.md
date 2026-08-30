# Changelog

All notable changes to this project are documented here.

## Unreleased

### Fixed

- Dry-run mode now pauses scheduled delivery as well as conversational sends, without querying Messages or modifying outbox records. Pending and retrying scheduled messages remain eligible when live mode resumes.
- Regression tests cover unchanged outbox records, delivery after leaving dry-run mode, and no-send conversational behavior; unit tests block unmocked external commands.

### Changed

- Setup now uses one supervised live test in the operator's private chat before expanding to family chats and background operation. Dry-run and synthetic model tests remain optional troubleshooting tools.
- README, setup prompt, configuration/security notes, and installer guidance now describe the same workflow and explain how queued messages behave when live mode resumes.

## [0.2.0] - 2026-08-29

### Added

- Optional, exact `@persona` routing with deterministic local help and validation.
- Time-bounded scheduled-message duplicate checks so old identical messages do not suppress a new recurrence.
- Preview-first cleanup for delivered and canceled outbox records.
- Private-by-default dry-run logging.
- Supported uninstall workflow and explicit update instructions.
- Supervised Codex setup prompt, MIT license, version output, and expanded safety tests.

### Changed

- Configured history limits from 1–50 are now honored exactly.
- Sensitive and attachment replies ask the sender to contact the administrator directly instead of claiming an unimplemented notification.
- Documentation now describes Codex isolation precisely and identifies quiet hours, mention-only activation, serialized processing, and macOS integration testing as explicit boundaries.
- ChatGPT subscription authentication is the documented default; API-key authentication is an advanced alternative.

## [0.1.0] - 2026-08-29

- Initial sanitized public reference implementation.

[0.2.0]: https://github.com/mcornelia/family-ai-chatbot/releases/tag/v0.2.0
[0.1.0]: https://github.com/mcornelia/family-ai-chatbot/commit/a8cc6e1
