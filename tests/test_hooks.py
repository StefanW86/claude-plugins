"""Tests der Hook-Skripte im Plugin stefan. Ausführen: python3 -m unittest discover tests"""
import json
import os
import shutil
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

    def test_commit_after_branch_switch_in_same_command_allowed(self):
        for sw in ("git checkout -b feat/x", "git switch -c feat/x", "git switch feat/x"):
            self.assertIsNone(self.bash(f"cd {self.main} && {sw} && git add -A && git commit -m x"), sw)
        self.assertEqual(self.bash(f"cd {self.main} && git switch -c feat/x && git switch main && git commit -m x"), "deny")

    def test_commit_with_co_author_trailer_denied(self):
        self.assertEqual(self.bash('git commit -qm "feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"'), "deny")
        self.assertEqual(self.bash("git commit -F- <<'EOF'\nfeat: x\n\nco-authored-by: A <a@b>\nEOF"), "deny")
        self.assertEqual(self.bash('git commit -m x --trailer "Co-authored-by: A <a@b>"'), "deny")
        self.assertIsNone(self.bash("grep -rn Co-Authored-By . && git log -1"))

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



FAKE_TERRAFORM = """#!/bin/sh
# Ersatz für terraform fmt -check: unformatiert ist, was UNFORMATTED enthält
PATH=/usr/bin:/bin
[ "$1" = fmt ] || exit 1
shift
files=$(for a in "$@"; do case "$a" in -*) ;; *) echo "$a" ;; esac; done)
[ -n "$files" ] || case " $* " in *" -recursive "*) files=$(find . -name '*.tf') ;; *) files=$(ls ./*.tf 2>/dev/null) ;; esac
[ -n "$files" ] && grep -qs UNFORMATTED $files && exit 3
exit 0
"""


class TerraformGuardTest(unittest.TestCase):
    tearDown, decision, bash, ps = GuardTest.tearDown, GuardTest.decision, GuardTest.bash, GuardTest.ps

    def setUp(self):
        GuardTest.setUp(self)
        self.bin = os.path.join(self.home, "bin")
        os.makedirs(self.bin)
        for tool in ("git", "python3"):
            os.symlink(shutil.which(tool), os.path.join(self.bin, tool))
        self.env["PATH"] = self.bin
        self.infra = make_repo(os.path.join(self.home, "dev", "Infra"), branch="feat/x")

    def with_terraform(self):
        path = os.path.join(self.bin, "terraform")
        with open(path, "w") as f:
            f.write(FAKE_TERRAFORM)
        os.chmod(path, 0o755)

    def write(self, rel, text):
        path = os.path.join(self.infra, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def test_terraform_changes_ask(self):
        for c in ("terraform apply", "terraform -chdir=infra apply -auto-approve", "sudo terraform destroy",
                  "terraform state rm aws_instance.web", "terraform import aws_instance.web i-1",
                  "terraform plan -out p && terraform apply p"):
            self.assertEqual(self.bash(c), "ask", c)
        self.assertEqual(self.ps("terraform.exe apply"), "ask")

    def test_terraform_read_only_allowed(self):
        for c in ("terraform init -backend=false", "terraform plan", "terraform validate", "terraform fmt -recursive",
                  "terraform test", "terraform state list", "terraform show", "echo 'terraform apply'"):
            self.assertIsNone(self.bash(c), c)

    def test_commit_with_unformatted_terraform_denied(self):
        self.with_terraform()
        self.write("infra/main.tf", "UNFORMATTED")
        self.assertEqual(self.bash("git add -A && git commit -m x", cwd=self.infra), "deny")
        self.assertEqual(self.bash("git commit -m x", cwd=os.path.join(self.infra, "infra")), "deny")

    def test_commit_with_formatted_terraform_allowed(self):
        self.with_terraform()
        self.write("main.tf", "ok")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    def test_commit_ignores_terraform_outside_git(self):
        self.with_terraform()
        self.write(".gitignore", ".terraform/\n")
        self.write(".terraform/modules/vpc/main.tf", "UNFORMATTED")
        self.write("main.tf", "ok")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    def test_commit_checks_unusual_file_names(self):
        self.with_terraform()
        self.write("mäin.tf", "UNFORMATTED")
        self.assertEqual(self.bash("git add -A && git commit -m x", cwd=self.infra), "deny")

    def test_commit_with_deleted_terraform_file_allowed(self):
        self.with_terraform()
        self.write("main.tf", "ok")
        self.write("old.tf", "ok")
        git(self.infra, "add", "-A")
        os.remove(os.path.join(self.infra, "old.tf"))
        self.assertIsNone(self.bash("git commit -am x", cwd=self.infra))

    def test_commit_with_terraform_state_plan_or_tfvars_denied(self):
        for f in ("terraform.tfstate", "env/terraform.tfstate.backup", ".terraform/providers/p",
                  ".terraform.lock.hcl", "infra/.terraform.lock.hcl", "prod.tfplan", "prod.tfvars",
                  "env/secrets.auto.tfvars.json"):
            self.write(f, "x")
            git(self.infra, "add", "-f", f)
            self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "deny", f)
            git(self.infra, "rm", "-q", "-r", "--cached", f)

    def test_commit_with_untracked_tfvars_denied(self):
        self.write("prod.tfvars", "x")
        self.assertEqual(self.bash("git add -A && git commit -m x", cwd=self.infra), "deny")

    def test_commit_with_ignored_state_and_tfvars_example_allowed(self):
        self.write(".gitignore", "*.tfstate\n*.tfvars\n")
        self.write("terraform.tfstate", "x")
        self.write("prod.tfvars", "x")
        self.write("prod.tfvars.example", "x")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    def test_terraform_binary_inside_repo_not_run(self):
        self.write("main.tf", "ok")
        self.write("terraform", FAKE_TERRAFORM)
        os.chmod(os.path.join(self.infra, "terraform"), 0o755)
        self.env["PATH"] = f"{self.bin}:{self.infra}"
        self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "ask")

    def test_terraform_from_path_below_working_dir_runs(self):
        self.write("main.tf", "UNFORMATTED")
        self.write("tools/terraform", FAKE_TERRAFORM)
        os.chmod(os.path.join(self.infra, "tools", "terraform"), 0o755)
        self.env["PATH"] = f"{self.bin}:{os.path.join(self.infra, 'tools')}"
        self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "deny")

    def test_commit_with_terraform_but_no_binary_asks(self):
        self.write("main.tf", "ok")
        self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "ask")

    def test_commit_without_terraform_files_needs_no_binary(self):
        self.write("README.md", "UNFORMATTED")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))


class PowerShellGuardTest(unittest.TestCase):
    tearDown, decision, bash, ps = GuardTest.tearDown, GuardTest.decision, GuardTest.bash, GuardTest.ps

    def setUp(self):
        GuardTest.setUp(self)
        self.repo = make_repo(os.path.join(self.home, "dev", "Scripts"), branch="feat/x")

    def write(self, rel, data):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data if isinstance(data, bytes) else data.encode("utf-8"))

    def commit(self):
        return self.bash("git add -A && git commit -m x", cwd=self.repo)

    def test_non_ascii_without_bom_denied(self):
        for f in ("run.ps1", "mod/Tools.psm1", "mod/Tools.psd1"):
            self.write(f, "Write-Output 'Größe'\n")
            self.assertEqual(self.commit(), "deny", f)
            os.remove(os.path.join(self.repo, f))

    def test_requires_5_1_without_bom_denied(self):
        self.write("run.ps1", "#Requires -Version 5.1\nWrite-Output 'Größe'\n")
        self.assertEqual(self.commit(), "deny")

    def test_bom_or_ascii_allowed(self):
        self.write("bom.ps1", b"\xef\xbb\xbfWrite-Output 'Gr\xc3\xb6\xc3\x9fe'\n")
        self.write("utf16.ps1", "Write-Output 'Größe'\n".encode("utf-16"))
        self.write("ascii.ps1", "Write-Output 'Groesse'\n")
        self.assertIsNone(self.commit())

    def test_core_only_script_allowed(self):
        self.write("a.ps1", "#Requires -Version 7.2\nWrite-Output 'Größe'\n")
        self.write("b.ps1", "#requires -PSEdition Core\nWrite-Output 'Größe'\n")
        self.assertIsNone(self.commit())

    def test_ignored_and_deleted_scripts_not_checked(self):
        self.write(".gitignore", "out/\n")
        self.write("out/tmp.ps1", "Write-Output 'Größe'\n")
        self.write("old.ps1", "Write-Output 'ok'\n")
        git(self.repo, "add", "-A")
        os.remove(os.path.join(self.repo, "old.ps1"))
        self.assertIsNone(self.bash("git commit -am x", cwd=self.repo))

    def test_powershell_tool_commit_checked(self):
        self.write("run.ps1", "Write-Output 'Größe'\n")
        git(self.repo, "add", "-A")
        self.assertEqual(self.ps("git commit -m x", cwd=self.repo), "deny")


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

    def test_branch_scheme_of_project_matches_by_number_or_slug(self):
        self.write_spec([("T01", "todo", [])], closing="todo")
        for branch in ("feature/x", "feature/0003-x", "bug/0003-anderer-name"):
            git(self.repo, "switch", "-q", "-c", branch)
            self.assertIn("T01", self.stop(), branch)
        git(self.repo, "switch", "-q", "-c", "feature/x-y")
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
