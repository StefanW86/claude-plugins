"""Tests der Hook-Skripte im Plugin stefan. Ausführen: python3 -m unittest discover tests"""
import json
import os
import subprocess
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins", "stefan", "scripts")
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def run_script(name, stdin, env):
    if not isinstance(stdin, str):
        stdin = json.dumps(stdin)
    return subprocess.run(["python3", os.path.join(SCRIPTS, name)], input=stdin,
                          capture_output=True, text=True, env=env)


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


def make_repo(path, branch="main", commit=True):
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q", "-b", branch)
    if commit:
        git(path, "commit", "-q", "--allow-empty", "-m", "init")
    return path


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.realpath(self.tmp.name)
        self.env = {**os.environ, **GIT_ENV, "HOME": self.home}
        self.dev = make_repo(os.path.join(self.home, "dev", "App"), branch="feat/0001-x")
        self.main = make_repo(os.path.join(self.home, "dev", "Other"))
        self.prod = make_repo(os.path.join(self.home, "app"))

    def tearDown(self):
        self.tmp.cleanup()

    def decision(self, tool, tool_input, cwd=None):
        r = run_script("guard.py", {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or self.dev}, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else None

    def bash(self, command, cwd=None):
        return self.decision("Bash", {"command": command}, cwd)

    def test_kill_by_name_denied(self):
        self.assertEqual(self.bash("pkill -f 'next dev'"), "deny")
        self.assertEqual(self.bash("ls && sudo killall node"), "deny")

    def test_kill_as_text_allowed(self):
        self.assertIsNone(self.bash("echo 'pkill -f x' && grep -r killall ."))
        self.assertIsNone(self.bash("kill -n 9 4711"))

    def test_commit_on_main_denied(self):
        self.assertEqual(self.bash("git commit -m x", cwd=self.main), "deny")
        self.assertEqual(self.bash(f"cd {self.main} && git add -A && git commit -m x"), "deny")
        self.assertEqual(self.bash(f"git -C {self.main} commit -m x"), "deny")

    def test_commit_on_branch_allowed(self):
        self.assertIsNone(self.bash("git add -A && git commit -m \"$(cat <<'EOF'\nfeat: x\n\nmain don't\nEOF\n)\""))

    def test_first_commit_and_merge_on_main_allowed(self):
        fresh = make_repo(os.path.join(self.home, "dev", "New"), commit=False)
        self.assertIsNone(self.bash("git commit -m init", cwd=fresh))
        open(os.path.join(self.main, ".git", "MERGE_HEAD"), "w").close()
        self.assertIsNone(self.bash("git commit --no-edit", cwd=self.main))

    def test_push_to_main_allowed(self):
        self.assertIsNone(self.bash("git push origin main"))
        self.assertIsNone(self.bash("git push -u origin HEAD:main"))
        self.assertIsNone(self.bash("git push", cwd=self.main))

    def test_push_feature_allowed(self):
        self.assertIsNone(self.bash("git push -u origin feat/0001-x"))
        self.assertIsNone(self.bash("git push origin --delete feat/0001-x"))
        self.assertIsNone(self.bash("git push"))

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
        self.assertEqual(self.bash(f"git -C {self.prod} reset --hard"), "deny")

    def test_reading_prod_allowed(self):
        self.assertIsNone(self.bash(f"git -C {self.prod} log --oneline -3 && cat {self.prod}/.env > /dev/null"))

    def test_write_command_into_prod_asks(self):
        self.assertEqual(self.bash(f"sed -i 's/a/b/' {self.prod}/compose.yml"), "ask")
        self.assertEqual(self.bash(f"cat <<'EOF' > {self.prod}/notes.txt\nx\nEOF"), "ask")

    def ps(self, command, cwd=None):
        return self.decision("PowerShell", {"command": command}, cwd)

    def test_powershell_kill_by_name_denied(self):
        self.assertEqual(self.ps("Stop-Process -Name node -Force"), "deny")
        self.assertEqual(self.ps("Get-Process node | Stop-Process"), "deny")
        self.assertEqual(self.ps("taskkill /IM node.exe /F"), "deny")
        self.assertEqual(self.ps("kill -Name dotnet"), "deny")

    def test_powershell_kill_by_pid_allowed(self):
        self.assertIsNone(self.ps("Stop-Process -Id 4711"))
        self.assertIsNone(self.ps("taskkill /PID 4711 /F"))

    def test_powershell_git_rules(self):
        self.assertEqual(self.ps(f"Set-Location {self.main}; git commit -m x"), "deny")
        self.assertEqual(self.ps("git pull", cwd=self.prod), "deny")
        self.assertIsNone(self.ps("git commit -m x"))

    def test_powershell_write_into_prod_asks(self):
        prod_win = self.prod.replace("/", "\\")
        self.assertEqual(self.ps(f"Remove-Item -Recurse {prod_win}\\node_modules"), "ask")
        self.assertEqual(self.ps(f"'x' | Out-File {self.prod}/a.txt"), "ask")
        self.assertIsNone(self.ps(f"Get-Content {prod_win}\\compose.yml"))

    def test_utf8_input(self):
        r = subprocess.run(["python3", os.path.join(SCRIPTS, "guard.py")], capture_output=True, env=self.env,
                           input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "pkill ä"},
                                             "cwd": self.dev}, ensure_ascii=False).encode("utf-8"))
        self.assertIn(b'"deny"', r.stdout)

    def test_launcher_runs_guard(self):
        r = subprocess.run(["sh", os.path.join(SCRIPTS, "run.sh"), "guard.py"], capture_output=True, text=True,
                           env=self.env, input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "pkill x"},
                                                           "cwd": self.dev}))
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_invalid_input_ignored(self):
        r = run_script("guard.py", "kein json", self.env)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


class OpenTasksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = os.path.realpath(self.tmp.name)
        self.repo = make_repo(os.path.join(self.base, "App"), branch="feat/0003-x")
        os.makedirs(os.path.join(self.repo, "docs", "specs"))
        self.env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}

    def tearDown(self):
        self.tmp.cleanup()

    def write_spec(self, tasks, status="In Progress", closing=None, nnnn="0003"):
        spec = f"docs/specs/{nnnn}-x.md"
        with open(os.path.join(self.repo, spec), "w") as f:
            f.write(f"# {nnnn} – Spec: X\n\n- **Status:** {status} · **Datum:** 2026-11-21\n")
        data = {"spec": spec, "mode": "small",
                "tasks": [{"id": tid, "status": st, "dependsOn": deps} for tid, st, deps in tasks]}
        if closing:
            data["closing"] = {"status": closing, "notes": ""}
        with open(os.path.join(self.repo, f"docs/specs/{nnnn}-x.tasks.json"), "w") as f:
            json.dump(data, f)

    def stop(self, cwd=None):
        """Hinweis an Claude (= weiterarbeiten) oder None (= darf stoppen)."""
        r = run_script("open-tasks.py", {"hook_event_name": "Stop", "stop_hook_active": False,
                                         "cwd": cwd or self.repo}, self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout.strip() else None

    def test_open_task_blocks_stop(self):
        self.write_spec([("T01", "done", []), ("T02", "todo", ["T01"])], closing="todo")
        self.assertIn("T02", self.stop())

    def test_blocked_chain_allows_stop(self):
        self.write_spec([("T01", "blocked", []), ("T02", "todo", ["T01"]), ("T03", "todo", ["T02"])], closing="todo")
        self.assertIsNone(self.stop())

    def test_independent_task_after_blocked_blocks_stop(self):
        self.write_spec([("T01", "blocked", []), ("T02", "in_progress", [])], closing="todo")
        msg = self.stop()
        self.assertIn("T02", msg)
        self.assertNotIn("T01", msg)

    def test_open_closing_blocks_stop(self):
        self.write_spec([("T01", "done", [])], closing="todo")
        self.assertIn("Abschluss", self.stop())

    def test_finished_allows_stop(self):
        self.write_spec([("T01", "done", [])], closing="done")
        self.assertIsNone(self.stop())

    def test_old_format_without_closing_allows_stop(self):
        self.write_spec([("T01", "done", [])])
        self.assertIsNone(self.stop())

    def test_inactive_unless_in_progress_on_matching_branch(self):
        self.write_spec([("T01", "todo", [])], status="Ready", closing="todo")
        self.assertIsNone(self.stop())
        self.write_spec([("T01", "todo", [])], closing="todo", nnnn="0004")
        self.assertIsNone(self.stop())
        git(self.repo, "switch", "-q", "-c", "fix/y")
        self.write_spec([("T01", "todo", [])], closing="todo")
        self.assertIsNone(self.stop())

    def test_project_dir_wins_over_cwd(self):
        self.write_spec([("T01", "todo", [])], closing="todo")
        clone = make_repo(os.path.join(self.base, "Clone"), branch="feat/0003-x")
        self.env["CLAUDE_PROJECT_DIR"] = self.repo
        self.assertIn("T01", self.stop(cwd=clone))

    def test_outside_repo_and_invalid_input_allow_stop(self):
        self.assertIsNone(self.stop(cwd=self.base))
        r = run_script("open-tasks.py", "kein json", self.env)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
