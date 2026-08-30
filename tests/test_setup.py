"""Setup checks use temporary fixtures only, never live Messages or model access."""

from contextlib import redirect_stderr, redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("setup_courier", ROOT / "courier.py")
courier = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(courier)


class EnableRepliesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="family-ai-setup-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config_path = self.root / "config.json"
        self.outbox = self.root / "outbox"
        self.config = json.loads((ROOT / "config.example.json").read_text())
        self.config["contacts"] = [{"name": "Private test", "chat_id": "123"}]
        self.config["custom_setting"] = {"keep": "unchanged"}
        self.write_config(self.config)
        self.output = io.StringIO()
        self.errors = io.StringIO()
        for name in ("run_checked", "model_reply", "recent_history", "send_reply", "daemon"):
            guard = mock.patch.object(
                courier, name, side_effect=AssertionError(f"Setup must not call {name}")
            )
            guard.start()
            self.addCleanup(guard.stop)

    def write_config(self, config):
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        self.config_path.chmod(0o600)

    def enable(self):
        with redirect_stdout(self.output), redirect_stderr(self.errors):
            return courier.enable_replies_command(self.config_path, self.outbox)

    def test_enables_only_sending_setting_and_keeps_private_permissions(self):
        self.assertEqual(self.enable(), 0)
        expected = dict(self.config, dry_run=False)
        self.assertEqual(courier.load_json(self.config_path), expected)
        self.assertEqual(stat.S_IMODE(self.config_path.stat().st_mode), 0o600)
        self.assertEqual(set(self.root.iterdir()), {self.config_path})
        self.assertIn("No service started or message sent", self.output.getvalue())
        self.assertNotIn("123", self.output.getvalue())

    def test_repeating_command_is_a_no_op(self):
        self.assertEqual(self.enable(), 0)
        before = self.config_path.read_bytes(), self.config_path.stat().st_mtime_ns
        self.assertEqual(self.enable(), 0)
        self.assertEqual(before, (self.config_path.read_bytes(), self.config_path.stat().st_mtime_ns))
        self.assertIn("already enabled", self.output.getvalue())

    def test_missing_configuration_is_not_created(self):
        self.config_path.unlink()
        self.assertEqual(self.enable(), 1)
        self.assertFalse(self.config_path.exists())

    def test_invalid_configuration_is_never_changed(self):
        examples = []
        for chat_id in ("REPLACE_WITH_CHAT_ROWID", "private@example.test", "0", "-2", 1.5, True):
            candidate = copy.deepcopy(self.config)
            candidate["contacts"][0]["chat_id"] = chat_id
            examples.append(candidate)
        examples.extend([
            dict(self.config, assistant_name="REPLACE_WITH_NAME"),
            dict(self.config, contacts=[]),
            dict(self.config, dry_run="true"),
            dict(self.config, contacts=self.config["contacts"] * 2),
        ])
        for candidate in examples:
            with self.subTest(candidate=candidate):
                self.write_config(candidate)
                before = self.config_path.read_bytes()
                self.assertEqual(self.enable(), 1)
                self.assertEqual(self.config_path.read_bytes(), before)
        self.assertNotIn("private@example.test", self.errors.getvalue())

    def test_malformed_json_is_never_changed(self):
        self.config_path.write_text('{"private": invalid}', encoding="utf-8")
        before = self.config_path.read_bytes()
        self.assertEqual(self.enable(), 1)
        self.assertEqual(self.config_path.read_bytes(), before)

    def test_symlink_configuration_is_not_replaced(self):
        original = self.root / "original.json"
        self.config_path.rename(original)
        self.config_path.symlink_to(original)
        self.assertEqual(self.enable(), 1)
        self.assertTrue(self.config_path.is_symlink())
        self.assertTrue(courier.load_json(original)["dry_run"])

    def test_unfinished_or_unreadable_outbox_blocks_enable_without_changes(self):
        self.outbox.mkdir()
        record = self.outbox / "test.json"
        for value in ('{"status":"pending"}', '{"status":"retrying"}', '{"status":"unknown"}', 'broken'):
            with self.subTest(value=value):
                record.write_text(value, encoding="utf-8")
                before = self.config_path.read_bytes(), record.read_bytes()
                self.assertEqual(self.enable(), 1)
                self.assertEqual(before, (self.config_path.read_bytes(), record.read_bytes()))

    def test_terminal_outbox_records_and_history_are_preserved(self):
        self.outbox.mkdir()
        state = self.root / "state.json"
        state.write_text('{"contacts":{"123":{"last_rowid":99}}}', encoding="utf-8")
        for status in ("delivered", "canceled"):
            (self.outbox / f"{status}.json").write_text(json.dumps({"status":status}), encoding="utf-8")
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in [state, *self.outbox.iterdir()]}
        self.assertEqual(self.enable(), 0)
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in before})

    def test_configured_outbox_is_checked_without_an_override(self):
        self.outbox.mkdir()
        (self.outbox / "test.json").write_text('{"status":"pending"}', encoding="utf-8")
        self.write_config(dict(self.config, outbox_path=str(self.outbox)))
        with redirect_stderr(self.errors):
            self.assertEqual(courier.enable_replies_command(self.config_path, None), 1)
        self.assertTrue(courier.load_json(self.config_path)["dry_run"])

    def test_failed_atomic_replace_preserves_original(self):
        before = self.config_path.read_bytes()
        with mock.patch.object(Path, "replace", side_effect=OSError("simulated failure")):
            self.assertEqual(self.enable(), 1)
        self.assertEqual(self.config_path.read_bytes(), before)
        self.assertEqual(set(self.root.iterdir()), {self.config_path})

    def test_cli_routes_to_enable_without_starting_daemon(self):
        with mock.patch("sys.argv", [
            "courier.py", "--config", str(self.config_path),
            "--outbox", str(self.outbox), "enable-replies",
        ]), redirect_stdout(self.output):
            self.assertEqual(courier.main(), 0)
        self.assertFalse(courier.load_json(self.config_path)["dry_run"])

    def test_setup_flow_enables_one_reply_and_preserves_restart_cursor(self):
        state_path = self.root / "state.json"
        state = {"contacts": {"123": {"last_rowid": 0, "name": "Private test"}}}
        contact = self.config["contacts"][0]
        event = {"id": 1, "text": "Hello", "is_from_me": False}
        with (
            mock.patch.object(courier, "recent_history", return_value=[event]),
            mock.patch.object(courier, "model_reply", return_value="Hello back!"),
            mock.patch.object(courier, "send_reply") as send,
            mock.patch.object(courier, "current_high_water") as baseline,
        ):
            courier.process_event(self.config, state, state_path, contact, event)
            send.assert_not_called()
            before_enable = state_path.read_bytes()
            self.assertEqual(self.enable(), 0)
            self.assertEqual(state_path.read_bytes(), before_enable)
            enabled = courier.load_json(self.config_path)
            courier.process_event(enabled, state, state_path, contact, dict(event, id=2))
            send.assert_called_once()
            courier.process_event(enabled, state, state_path, contact, dict(event, id=3, is_from_me=True))
            send.assert_called_once()
            restarted = courier.initialize_state(enabled, state_path)
            baseline.assert_not_called()
            courier.process_event(enabled, restarted, state_path, contact, dict(event, id=2))
            send.assert_called_once()
            courier.process_event(enabled, restarted, state_path, contact, dict(event, id=4))
            self.assertEqual(send.call_count, 2)


if __name__ == "__main__":
    unittest.main()
