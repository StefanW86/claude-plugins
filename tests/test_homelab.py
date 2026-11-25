"""Tests des Schutz-Hooks im Plugin stefan-homelab. Ausführen: python -m unittest discover tests"""
import filecmp
import json
import os
import tempfile
import unittest

from helpers import GIT_ENV, ROOT, make_repo, q, run_script

PLUGINS = os.path.join(ROOT, "plugins")
GUARD = os.path.join(PLUGINS, "stefan-homelab", "scripts", "prod_guard.py")


class ProdGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.realpath(self.tmp.name)
        self.env = {**os.environ, **GIT_ENV, "HOME": self.home, "USERPROFILE": self.home}
        self.dev = make_repo(os.path.join(self.home, "dev", "App"), branch="feature/0001-x")
        self.prod = make_repo(os.path.join(self.home, "app"))

    def tearDown(self):
        self.tmp.cleanup()

    def decision(self, tool, tool_input, cwd=None):
        r = run_script(GUARD, {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or self.dev}, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None

    def bash(self, command, cwd=None):
        return self.decision("Bash", {"command": command}, cwd)

    def ps(self, command, cwd=None):
        return self.decision("PowerShell", {"command": command}, cwd)

    def test_edit_in_prod_denied(self):
        self.assertEqual(self.decision("Edit", {"file_path": os.path.join(self.prod, "src", "a.ts")}), "deny")
        self.assertEqual(self.decision("Write", {"file_path": os.path.join(self.prod, "compose.yml")}), "deny")

    def test_prod_env_work_and_dev_allowed(self):
        work = make_repo(os.path.join(self.home, "app-work"))
        self.assertIsNone(self.decision("Write", {"file_path": os.path.join(self.prod, ".env")}))
        self.assertIsNone(self.decision("Edit", {"file_path": os.path.join(work, "a.ts")}))
        self.assertIsNone(self.decision("Edit", {"file_path": os.path.join(self.dev, "a.ts")}))

    def test_git_change_in_prod_denied(self):
        self.assertEqual(self.bash("git pull", cwd=self.prod), "deny")
        self.assertEqual(self.bash(f"git -C {q(self.prod)} reset --hard"), "deny")
        self.assertEqual(self.ps("git pull", cwd=self.prod), "deny")
        self.assertEqual(self.ps(f"Set-Location {q(self.prod)}; git switch -c feature/x"), "deny")

    def test_reading_prod_allowed(self):
        self.assertIsNone(self.bash(f"git -C {q(self.prod)} log --oneline -3 && cat {q(self.prod)}/.env > /dev/null"))

    def test_write_command_into_prod_asks(self):
        self.assertEqual(self.bash(f"sed -i 's/a/b/' {q(self.prod)}/compose.yml"), "ask")
        self.assertEqual(self.bash(f"cat <<'EOF' > {q(self.prod)}/notes.txt\nx\nEOF"), "ask")

    def test_powershell_write_into_prod_asks(self):
        prod_win = self.prod.replace("/", "\\")
        self.assertEqual(self.ps(f"Remove-Item -Recurse {prod_win}\\node_modules"), "ask")
        self.assertEqual(self.ps(f"'x' | Out-File {q(self.prod)}/a.txt"), "ask")
        self.assertIsNone(self.ps(f"Get-Content {prod_win}\\compose.yml"))

    def test_work_outside_prod_allowed(self):
        self.assertIsNone(self.bash("git add -A && git commit -m x && rm -rf build"))

    def test_invalid_input_ignored(self):
        r = run_script(GUARD, "kein json", self.env)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


class SharedParserTest(unittest.TestCase):
    def test_copies_identical(self):
        a, b = (os.path.join(PLUGINS, p, "scripts", "shellparse.py") for p in ("stefan", "stefan-homelab"))
        self.assertTrue(filecmp.cmp(a, b, shallow=False), "shellparse.py muss in beiden Plugins gleich sein")


if __name__ == "__main__":
    unittest.main()
