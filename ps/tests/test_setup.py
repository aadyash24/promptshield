import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from ps import launch, setup


class DiscoveryTests(unittest.TestCase):
    def test_mac_app_without_path_entry(self):
        app = Path("/Applications/Ollama.app/Contents/Resources/ollama")
        with patch.object(launch.sys, "platform", "darwin"), patch.object(
            launch.shutil, "which", return_value=None
        ), patch.object(Path, "is_file", autospec=True, side_effect=lambda path: path == app):
            self.assertEqual(launch.find_ollama(), app)

    def test_windows_portable_has_priority(self):
        with patch.object(launch.sys, "platform", "win32"), patch.object(
            launch.shutil, "which", return_value="other/ollama.exe"
        ), patch.object(Path, "is_file", return_value=True):
            self.assertEqual(launch.find_ollama(), launch.OLLAMA_EXE)

    def test_only_portable_uses_project_model_directory(self):
        with patch.dict(launch.os.environ, {}, clear=True):
            self.assertNotIn("OLLAMA_MODELS", launch.ollama_environment(Path("/usr/local/bin/ollama")))
            self.assertEqual(launch.ollama_environment(launch.OLLAMA_EXE)["OLLAMA_MODELS"], str(launch.OLLAMA_MODELS))


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.report = Mock()
        self.tags = {"models": [{"name": launch.DEFAULT_MODEL}]}
        for name, target, value in [
            ("find", "ps.launch.find_ollama", Path("ollama")),
            ("running", "ps.launch.running_service", self.tags),
            ("installed", "ps.get_model.is_installed", True),
            ("stop", "ps.launch.stop_services", None),
            ("popen", "ps.launch.subprocess.Popen", Mock()),
            ("pull", "ps.setup.pull_model", None),
        ]:
            patcher = patch(target, return_value=value)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)

    def test_existing_service_needs_no_cli_and_is_not_stopped(self):
        self.find.return_value = None
        self.assertEqual(setup.install(self.report), 0)
        self.popen.assert_not_called()
        self.pull.assert_not_called()
        self.stop.assert_called_once_with([])

    def test_missing_mac_runtime_has_actionable_error(self):
        self.find.return_value = None
        self.running.return_value = None
        with patch.object(setup.sys, "platform", "darwin"):
            self.assertEqual(setup.install(self.report), 1)
        self.assertIn("Install and open Ollama", self.report.call_args.args[2])
        self.popen.assert_not_called()

    def test_owned_service_is_cleaned_up_after_pull_failure(self):
        self.running.return_value = None
        self.pull.side_effect = RuntimeError("download failed")
        with patch.object(launch, "check_port"), patch.object(
            launch, "wait_for_json", return_value={"models": []}
        ):
            self.assertEqual(setup.install(self.report), 1)
        self.stop.assert_called_once_with([("Ollama", self.popen.return_value)])

    def test_pull_is_verified(self):
        self.running.side_effect = [{"models": []}, self.tags]
        self.assertEqual(setup.install(self.report), 0)
        self.pull.assert_called_once()

    def test_windows_missing_runtime_uses_existing_installer(self):
        self.find.return_value = None
        self.running.return_value = None
        with patch.object(setup.sys, "platform", "win32"), patch.object(
            setup.subprocess, "call", return_value=0
        ) as call:
            self.assertEqual(setup.install(self.report, True), 0)
        self.assertEqual(call.call_args.args[0][0], "powershell.exe")
        self.assertIn("-JsonProgress", call.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
