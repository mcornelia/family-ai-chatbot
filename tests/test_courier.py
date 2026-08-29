import importlib.util
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "courier.py"
SPEC = importlib.util.spec_from_file_location("courier", MODULE_PATH)
courier = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(courier)


class CourierTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "assistant_name": "Homebot",
            "owner_name": "Alex",
            "signature_mark": "✨",
            "contacts": [
                {"name": "Family Group", "chat_id": "3"},
            ],
            "imsg_path": "/opt/homebrew/bin/imsg",
        }

    def test_json_lines_ignores_noise(self):
        parsed = courier.parse_json_lines('noise\n{"id": 4, "text": "Hi"}\n')
        self.assertEqual(parsed, [{"id": 4, "text": "Hi"}])

    def test_message_helpers_accept_variants(self):
        message = {"rowid": "9", "body": " hello ", "isFromMe": "true"}
        self.assertEqual(courier.message_id(message), 9)
        self.assertEqual(courier.message_text(message), "hello")
        self.assertTrue(courier.is_from_me(message))

    def test_prompt_identifies_assistant_and_boundary(self):
        prompt = courier.build_prompt(
            self.config,
            {"name": "Jordan", "relationship": "household member"},
            [{"id": 1, "text": "Did Alex say yes?", "is_from_me": False}],
        )
        self.assertIn("Speak as Homebot, never as Alex", prompt)
        self.assertIn("Jordan: Did Alex say yes?", prompt)
        self.assertIn("Never make commitments", prompt)
        self.assertIn("✨ as Homebot's personal mark", prompt)

    def test_group_prompt_identifies_each_speaker(self):
        prompt = courier.build_prompt(
            self.config,
            {
                "name": "Family Group",
                "relationship": "a shared household conversation",
                "participants": {
                    "+15551230001": "Alex",
                    "+15551230002": "Jordan",
                },
            },
            [
                {
                    "id": 1,
                    "text": "What is this pump?",
                    "is_from_me": False,
                    "sender": "+15551230001",
                },
                {"id": 2, "text": "It is ethanol-free.", "is_from_me": True},
                {
                    "id": 3,
                    "text": "Who cares?",
                    "is_from_me": False,
                    "sender": "+15551230002",
                },
            ],
        )
        self.assertIn("private group iMessage conversation with Alex, Jordan", prompt)
        self.assertIn("Alex: What is this pump?", prompt)
        self.assertIn("Homebot: It is ethanol-free.", prompt)
        self.assertIn("Jordan: Who cares?", prompt)
        self.assertIn("addressing the latest speaker naturally", prompt)

    def test_validate_rejects_duplicate_chat(self):
        with self.assertRaises(ValueError):
            courier.validate_config(
                {
                    "contacts": [
                        {"name": "Alex", "chat_id": 1},
                        {"name": "Jordan", "chat_id": 1},
                    ]
                }
            )

    def test_validate_rejects_invalid_history_limit(self):
        config = dict(self.config, history_limit=0)
        with self.assertRaisesRegex(ValueError, "history_limit"):
            courier.validate_config(config)

    def test_model_reply_routes_to_codex(self):
        config = dict(
            self.config,
            codex_path="/Applications/ChatGPT.app/Contents/Resources/codex",
            codex_model="gpt-5.6-sol",
            codex_thinking="low",
        )
        with mock.patch.object(courier, "codex_model_reply", return_value="Hi there") as generate:
            self.assertEqual(courier.model_reply(config, "prompt"), "Hi there")
        generate.assert_called_once_with(
            Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
            "gpt-5.6-sol",
            "prompt",
            "low",
        )

    def test_codex_model_reply_is_ephemeral_read_only_and_uses_stdin(self):
        observed: dict[str, object] = {}

        def fake_run(command, timeout=30, input_text=None):
            observed["command"] = command
            observed["timeout"] = timeout
            observed["input_text"] = input_text
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text("A short reply\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with mock.patch.object(courier, "run_checked", side_effect=fake_run):
            reply = courier.codex_model_reply(
                Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
                "gpt-5.6-sol",
                "private prompt",
                "low",
            )

        command = observed["command"]
        self.assertEqual(reply, "A short reply")
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(command[-1], "-")
        self.assertEqual(observed["input_text"], "private prompt")
        self.assertNotIn("private prompt", command)

    def test_send_timeout_accepts_verified_late_success(self):
        with mock.patch.object(courier, "run_checked", side_effect=subprocess.TimeoutExpired("imsg", 60)):
            with mock.patch.object(
                courier,
                "recent_history",
                return_value=[{"id": 2, "is_from_me": True, "text": "Hello"}],
            ):
                courier.send_reply(Path("/opt/homebrew/bin/imsg"), {"chat_id": "1"}, "Hello")

    def test_send_timeout_rejects_unverified_send(self):
        with mock.patch.object(courier, "run_checked", side_effect=subprocess.TimeoutExpired("imsg", 60)):
            with mock.patch.object(courier, "recent_history", return_value=[]):
                with self.assertRaises(RuntimeError):
                    courier.send_reply(Path("/opt/homebrew/bin/imsg"), {"chat_id": "1"}, "Hello")

    def test_parse_datetime_requires_timezone(self):
        with self.assertRaises(ValueError):
            courier.parse_datetime("2026-08-24T19:00:00")
        parsed = courier.parse_datetime("2026-08-24T19:00:00-04:00")
        self.assertEqual(parsed.isoformat(), "2026-08-24T23:00:00+00:00")

    def test_queue_message_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = Path(temp)
            send_at = datetime(2026, 8, 24, 23, tzinfo=timezone.utc)
            now = datetime(2026, 8, 18, 12, tzinfo=timezone.utc)
            first = courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                send_at,
                "Special delivery",
                now=now,
            )
            second = courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                send_at,
                "Special delivery",
                now=now + timedelta(minutes=5),
            )
            self.assertEqual(first, second)
            self.assertEqual(len(list(outbox.glob("*.json"))), 1)

    def test_due_message_sends_and_verifies_once(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = Path(temp)
            now = datetime(2026, 8, 18, 23, tzinfo=timezone.utc)
            entry = courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                now - timedelta(minutes=1),
                "Special delivery",
                now=now - timedelta(days=1),
            )
            with mock.patch.object(
                courier,
                "recent_history",
                side_effect=[[], [{"id": 99, "is_from_me": True, "text": "Special delivery"}]],
            ):
                with mock.patch.object(courier, "send_reply") as send_reply:
                    results = courier.process_due_outbox(self.config, outbox, now=now)
            send_reply.assert_called_once()
            self.assertEqual(results[0]["status"], "delivered")
            saved = json.loads((outbox / f"{entry['id']}.json").read_text())
            self.assertEqual(saved["delivery_reason"], "sent_and_verified")
            self.assertTrue(saved["history_verified"])

    def test_successful_send_is_not_retried_when_history_lags(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = Path(temp)
            now = datetime(2026, 8, 19, 12, tzinfo=timezone.utc)
            entry = courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                now - timedelta(minutes=1),
                "Special delivery",
                now=now - timedelta(days=1),
            )
            with mock.patch.object(courier, "recent_history", return_value=[]):
                with mock.patch.object(courier, "send_reply") as send_reply:
                    results = courier.process_due_outbox(self.config, outbox, now=now)

            send_reply.assert_called_once()
            self.assertEqual(results[0]["status"], "delivered")
            saved = json.loads((outbox / f"{entry['id']}.json").read_text())
            self.assertEqual(saved["delivery_reason"], "send_command_succeeded")
            self.assertFalse(saved["history_verified"])

    def test_duplicate_check_ignores_messages_object_marker_and_whitespace(self):
        history = [
            {
                "id": 99,
                "is_from_me": True,
                "text": "Special\ufffc   delivery\nfrom Homebot",
            }
        ]
        self.assertTrue(
            courier.outgoing_message_exists(history, "Special delivery from Homebot")
        )

    def test_due_message_detects_existing_outgoing_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = Path(temp)
            now = datetime(2026, 8, 18, 23, tzinfo=timezone.utc)
            courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                now - timedelta(minutes=1),
                "Special delivery",
                now=now - timedelta(days=1),
            )
            history = [{"id": 99, "is_from_me": True, "text": "Special delivery"}]
            with mock.patch.object(courier, "recent_history", return_value=history):
                with mock.patch.object(courier, "send_reply") as send_reply:
                    results = courier.process_due_outbox(self.config, outbox, now=now)
            send_reply.assert_not_called()
            self.assertEqual(results[0]["delivery_reason"], "already_present")

    def test_failed_message_is_retained_for_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = Path(temp)
            now = datetime(2026, 8, 18, 23, tzinfo=timezone.utc)
            entry = courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                now - timedelta(minutes=1),
                "Special delivery",
                now=now - timedelta(days=1),
            )
            with mock.patch.object(courier, "recent_history", side_effect=RuntimeError("permission denied")):
                results = courier.process_due_outbox(self.config, outbox, now=now)
            self.assertEqual(results[0]["status"], "retrying")
            self.assertEqual(results[0]["attempts"], 1)
            saved = json.loads((outbox / f"{entry['id']}.json").read_text())
            self.assertIn("permission denied", saved["last_error"])
            self.assertEqual(
                courier.parse_datetime(saved["next_attempt_at"]),
                now + timedelta(seconds=courier.OUTBOX_RETRY_SECONDS),
            )

    def test_future_message_is_not_sent(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = Path(temp)
            now = datetime(2026, 8, 18, 23, tzinfo=timezone.utc)
            courier.queue_message_file(
                self.config,
                outbox,
                "Family Group",
                now + timedelta(hours=1),
                "Special delivery",
                now=now,
            )
            with mock.patch.object(courier, "send_reply") as send_reply:
                results = courier.process_due_outbox(self.config, outbox, now=now)
            send_reply.assert_not_called()
            self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
