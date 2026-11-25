"""Tests der Hook-Skripte im Plugin stefan. Ausführen: python -m unittest discover tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from helpers import GIT_ENV, ROOT, git, make_repo, q, run_script

SCRIPTS = os.path.join(ROOT, "plugins", "stefan", "scripts")
GUARD = os.path.join(SCRIPTS, "guard.py")
OPEN_TASKS = os.path.join(SCRIPTS, "open-tasks.py")
RUN_SH = os.path.join(SCRIPTS, "run.sh")
SH = shutil.which("sh")
TERRAFORM = shutil.which("terraform")
WINDOWS = os.name == "nt"


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.realpath(self.tmp.name)
        self.env = {**os.environ, **GIT_ENV, "HOME": self.home, "USERPROFILE": self.home}
        self.dev = make_repo(os.path.join(self.home, "dev", "App"), branch="feature/0001-x")
        self.main = make_repo(os.path.join(self.home, "dev", "Other"))

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

    def test_kill_by_name_denied(self):
        self.assertEqual(self.bash("pkill -f 'next dev'"), "deny")
        self.assertEqual(self.bash("ls && sudo killall node"), "deny")

    def test_kill_via_pid_lookup_denied(self):
        for c in ("kill $(pgrep -f 'next dev')", "pgrep -f next | xargs kill", "pgrep node | xargs -r kill -9",
                  "kill -9 `pidof node`"):
            self.assertEqual(self.bash(c), "deny", c)

    def test_kill_as_text_or_by_pid_allowed(self):
        for c in ("echo 'pkill -f x' && grep -r killall .", "kill -n 9 4711", "pgrep -fl next",
                  "kill $(lsof -ti :3000)", 'git commit -m "fix: kill nicht per pgrep"'):
            self.assertIsNone(self.bash(c), c)

    def test_commit_on_main_denied(self):
        self.assertEqual(self.bash("git commit -m x", cwd=self.main), "deny")
        self.assertEqual(self.bash(f"cd {q(self.main)} && git add -A && git commit -m x"), "deny")
        self.assertEqual(self.bash(f"git -C {q(self.main)} commit -m x"), "deny")

    def test_commit_on_branch_allowed(self):
        self.assertIsNone(self.bash("git add -A && git commit -m \"$(cat <<'EOF'\nfeat: x\n\nmain don't\nEOF\n)\""))

    def test_commit_after_branch_switch_in_same_command_allowed(self):
        for sw in ("git checkout -b feature/x", "git switch -c feature/x", "git switch feature/x"):
            self.assertIsNone(self.bash(f"cd {q(self.main)} && {sw} && git add -A && git commit -m x"), sw)
        self.assertEqual(self.bash(f"cd {q(self.main)} && git switch -c feature/x && git switch main && "
                                   "git commit -m x"), "deny")

    def test_commit_with_co_author_trailer_denied(self):
        self.assertEqual(self.bash('git commit -qm "feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"'), "deny")
        self.assertEqual(self.bash("git commit -F- <<'EOF'\nfeat: x\n\nco-authored-by: A <a@b>\nEOF"), "deny")
        self.assertEqual(self.bash('git commit -m x --trailer "Co-authored-by: A <a@b>"'), "deny")
        self.assertIsNone(self.bash("grep -rn Co-Authored-By . && git log -1"))

    def test_commit_with_co_author_in_message_file_denied(self):
        with open(os.path.join(self.dev, "msg.txt"), "w") as f:
            f.write("feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
        with open(os.path.join(self.dev, "ok.txt"), "w") as f:
            f.write("feat: x\n")
        for c in ("git commit -F msg.txt", "git commit --file=msg.txt", "git commit -aF msg.txt",
                  f"git -C {q(self.dev)} commit --file msg.txt"):
            self.assertEqual(self.bash(c, cwd=self.home if "-C" in c else None), "deny", c)
        self.assertIsNone(self.bash("git commit -F ok.txt"))

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
        self.assertIsNone(self.bash("git push -u origin feature/0001-x"))
        self.assertIsNone(self.bash("git push origin --delete feature/0001-x"))
        self.assertIsNone(self.bash("git push"))

    def test_repo_directly_under_home_is_not_protected(self):
        """Prod-Checkouts schützt nur stefan-homelab; unter Windows liegen normale Repos oft direkt im Profil."""
        repo = make_repo(os.path.join(self.home, "gitworkshop"))
        self.assertIsNone(self.bash("git switch -c feature/test && git commit -m test", cwd=repo))
        self.assertIsNone(self.decision("Edit", {"file_path": os.path.join(repo, "a.txt")}))

    def test_powershell_kill_by_name_denied(self):
        for c in ("Stop-Process -Name node -Force", "Get-Process node | Stop-Process", "taskkill /IM node.exe /F",
                  "kill -Name dotnet", "Get-Process node | kill", "Get-Process -Name node | Stop-Process -Force",
                  "Get-Process node | Stop-Process -ErrorAction SilentlyContinue", "Stop-Process -InputObject $p"):
            self.assertEqual(self.ps(c), "deny", c)

    def test_powershell_kill_by_pid_allowed(self):
        for c in ("Stop-Process -Id 4711", "taskkill /PID 4711 /F", "Get-Process -Id 4711 | Stop-Process",
                  "Stop-Process 4711", "kill 4711,4712",
                  "Stop-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess"):
            self.assertIsNone(self.ps(c), c)

    def test_powershell_git_rules(self):
        self.assertEqual(self.ps(f"Set-Location {q(self.main)}; git commit -m x"), "deny")
        self.assertIsNone(self.ps("git commit -m x"))

    def test_utf8_input(self):
        r = subprocess.run([sys.executable, GUARD], capture_output=True, env=self.env,
                           input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "pkill ä"},
                                             "cwd": self.dev}, ensure_ascii=False).encode("utf-8"))
        self.assertIn(b'"deny"', r.stdout)

    def test_invalid_input_ignored(self):
        r = run_script(GUARD, "kein json", self.env)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


@unittest.skipUnless(SH, "sh fehlt")
class LauncherTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = os.path.realpath(self.tmp.name)
        self.env = {**os.environ, "CLAUDE_PLUGIN_DATA": self.data}

    def tearDown(self):
        self.tmp.cleanup()

    def launch(self, env=None):
        request = json.dumps({"tool_name": "Bash", "tool_input": {"command": "pkill x"}, "cwd": self.data})
        return subprocess.run([SH, RUN_SH, "guard.py"], input=request, capture_output=True, encoding="utf-8",
                              env=env or self.env, timeout=30)

    def test_runs_guard(self):
        r = self.launch()
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny", r.stderr)

    @unittest.skipUnless(WINDOWS, "den Interpreter merkt sich run.sh nur unter Windows")
    def test_remembers_interpreter_and_recovers_from_stale_entry(self):
        cache = os.path.join(self.data, "python-path")
        self.launch()
        with open(cache) as f:
            self.assertTrue(os.path.isfile(f.read().strip()))
        with open(cache, "w") as f:
            f.write("C:\\fehlt\\python.exe\n")
        self.assertIn('"deny"', self.launch().stdout)
        with open(cache) as f:
            self.assertTrue(os.path.isfile(f.read().strip()))

    def test_without_python_warns_and_allows(self):
        empty = os.path.join(self.data, "leer")
        os.mkdir(empty)
        r = self.launch({**self.env, "PATH": empty})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Python 3 fehlt", json.loads(r.stdout)["systemMessage"])


UNFORMATTED = 'variable "x" {\ndefault="a"\n}\n'
FORMATTED = 'variable "x" {\n  default = "a"\n}\n'

# run-Block ohne command = plan (nur in Kommentar und Zeichenkette): legt echte Infrastruktur an
APPLY_RUN = """run "create" {
  # command = plan
  assert {
    condition     = output.name == "command = plan"
    error_message = "falscher Name"
  }
}
"""
PLAN_RUNS = """run "plan" {
  command = plan
  variables {
    name = "x"
  }
}

run "short" { command = plan }
"""
MOCKED = """mock_provider "azurerm" {}

run "apply_with_mock" {}
"""
needs_terraform = unittest.skipUnless(TERRAFORM, "terraform fehlt")


class TerraformGuardTest(unittest.TestCase):
    tearDown, decision, bash, ps = GuardTest.tearDown, GuardTest.decision, GuardTest.bash, GuardTest.ps

    def setUp(self):
        GuardTest.setUp(self)
        self.bin = os.path.join(self.home, "bin")
        os.makedirs(self.bin)
        self.env["PATH"] = self.only_git_on_path()
        self.infra = make_repo(os.path.join(self.home, "dev", "Infra"), branch="feature/x")

    def only_git_on_path(self):
        """PATH ohne terraform: unter POSIX ein Symlink auf git, unter Windows (Symlinks brauchen dort Adminrechte)
        der Ordner von git."""
        if WINDOWS:
            return os.path.dirname(shutil.which("git"))
        os.symlink(shutil.which("git"), os.path.join(self.bin, "git"))
        return self.bin

    def with_terraform(self):
        if WINDOWS:
            self.env["PATH"] += os.pathsep + os.path.dirname(TERRAFORM)
        else:
            os.symlink(TERRAFORM, os.path.join(self.bin, "terraform"))

    def terraform_in(self, rel_dir):
        """terraform zusätzlich in einem Ordner des Repos, vorn im PATH."""
        d = os.path.join(self.infra, rel_dir)
        os.makedirs(d, exist_ok=True)
        dest = os.path.join(d, os.path.basename(TERRAFORM))
        try:
            os.link(TERRAFORM, dest)
        except OSError:  # anderes Dateisystem
            shutil.copy2(TERRAFORM, dest)
        self.env["PATH"] = os.path.realpath(d) + os.pathsep + self.env["PATH"]

    def write(self, rel, text):
        path = os.path.join(self.infra, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def commit_all(self):
        git(self.infra, "add", "-A", "-f")
        git(self.infra, "commit", "-q", "-m", "bestand")

    def test_terraform_changes_ask(self):
        for c in ("terraform apply", "terraform -chdir=infra apply -auto-approve", "sudo terraform destroy",
                  "terraform state rm aws_instance.web", "terraform import aws_instance.web i-1",
                  "terraform plan -out p && terraform apply p", "terraform refresh", "terraform init -migrate-state",
                  "terraform -chdir=infra init -force-copy -migrate-state"):
            self.assertEqual(self.bash(c), "ask", c)
        self.assertEqual(self.ps("terraform.exe apply"), "ask")

    def test_terraform_read_only_allowed(self):
        for c in ("terraform init -backend=false", "terraform init -upgrade", "terraform plan",
                  "terraform plan -refresh-only", "terraform validate", "terraform fmt -recursive", "terraform test",
                  "terraform state list", "terraform show", "echo 'terraform apply'"):
            self.assertIsNone(self.bash(c), c)

    def test_terraform_test_with_real_infrastructure_asks(self):
        self.write("tests/main.tftest.hcl", APPLY_RUN)
        self.assertEqual(self.bash("terraform test", cwd=self.infra), "ask")
        self.assertEqual(self.bash("terraform -chdir=Infra test", cwd=os.path.dirname(self.infra)), "ask")
        self.assertEqual(self.ps("terraform.exe test", cwd=self.infra), "ask")

    def test_terraform_test_checks_each_run_block(self):
        self.write("main.tftest.hcl", 'run "plan" { command = plan }\n\nrun "apply" {\n  command = apply\n}\n')
        self.assertEqual(self.bash("terraform test", cwd=self.infra), "ask")

    def test_terraform_test_with_plan_or_mock_allowed(self):
        self.write("tests/plan.tftest.hcl", PLAN_RUNS)
        self.write("tests/mock.tftest.hcl", MOCKED)
        os.makedirs(os.path.join(self.infra, "tests", "ordner.tftest.hcl"))
        self.assertIsNone(self.bash("terraform test", cwd=self.infra))

    def test_terraform_test_honours_filter_and_test_directory(self):
        self.write("tests/plan.tftest.hcl", PLAN_RUNS)
        self.write("tests/apply.tftest.hcl", APPLY_RUN)
        self.write("integration/plan.tftest.hcl", PLAN_RUNS)
        self.assertIsNone(self.bash("terraform test -filter=tests/plan.tftest.hcl", cwd=self.infra))
        self.assertEqual(self.bash("terraform test -filter tests/apply.tftest.hcl", cwd=self.infra), "ask")
        self.assertIsNone(self.bash("terraform test -test-directory=integration", cwd=self.infra))

    def test_terraform_test_counts_command_only_in_run_block_itself(self):
        self.write("tests/nested.tftest.hcl", 'run "x" {\n  variables {\n    command = plan\n  }\n}\n')
        self.assertEqual(self.bash("terraform test", cwd=self.infra), "ask")

    def test_terraform_test_checks_json_files(self):
        self.write("tests/apply.tftest.json", '{"run": {"create": {}}}')
        self.assertEqual(self.bash("terraform test", cwd=self.infra), "ask")
        os.remove(os.path.join(self.infra, "tests", "apply.tftest.json"))
        self.write("tests/plan.tftest.json", '{"run": [{"a": {"command": "plan"}}, {"b": [{"command": "plan"}]}]}')
        self.write("tests/mock.tftest.json", '{"mock_provider": {"azurerm": {}}, "run": {"x": {}}}')
        self.assertIsNone(self.bash("terraform test", cwd=self.infra))

    def test_terraform_test_json_duplicates_and_bom(self):
        cases = [('{"run": {"x": {}}, "run": {"y": {"command": "plan"}}}', "ask"),
                 ('{"run": {"x": {}, "x": {"command": "plan"}}}', "ask"),
                 ('\ufeff{"run": {"x": {}}}', "ask"),
                 ('\ufeff{"run": {"x": {"command": "plan"}}}', None)]
        for text, expected in cases:
            self.write("tests/t.tftest.json", text)
            self.assertEqual(self.bash("terraform test", cwd=self.infra), expected, text)

    def test_terraform_test_unparsable_json_asks(self):
        for text in ('{"run": {"x": {}', '{"run": {"x": {}}, "n": ' + "1" * 5000 + "}", "[" * 100000):
            self.write("tests/bad.tftest.json", text)
            self.assertEqual(self.bash("terraform test", cwd=self.infra), "ask", text[:30])

    @unittest.skipIf(WINDOWS, "Geräte und FIFOs gibt es so nur unter POSIX")
    def test_terraform_test_skips_devices_and_fifos(self):
        self.write("tests/plan.tftest.hcl", PLAN_RUNS)
        os.symlink("/dev/zero", os.path.join(self.infra, "tests", "zero.tftest.hcl"))
        os.mkfifo(os.path.join(self.infra, "tests", "fifo.tftest.hcl"))
        self.assertIsNone(self.bash("terraform test", cwd=self.infra))

    def test_terraform_test_scan_is_linear(self):
        self.write("tests/nested.tftest.hcl", 'run "a" {\n  command = plan\n' * 20000)
        self.assertIsNone(self.bash("terraform test", cwd=self.infra))

    def test_terraform_test_with_huge_file_asks(self):
        self.write("tests/huge.tftest.hcl", PLAN_RUNS + "#" * (1 << 20))
        self.assertEqual(self.bash("terraform test", cwd=self.infra), "ask")

    @needs_terraform
    def test_commit_with_unformatted_terraform_denied(self):
        self.with_terraform()
        self.write("infra/main.tf", UNFORMATTED)
        self.assertEqual(self.bash("git add -A && git commit -m x", cwd=self.infra), "deny")
        self.assertEqual(self.bash("git commit -m x", cwd=os.path.join(self.infra, "infra")), "deny")

    @needs_terraform
    def test_commit_with_formatted_terraform_allowed(self):
        self.with_terraform()
        self.write("main.tf", FORMATTED)
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    @needs_terraform
    def test_commit_ignores_terraform_outside_git(self):
        self.with_terraform()
        self.write(".gitignore", ".terraform/\n")
        self.write(".terraform/modules/vpc/main.tf", UNFORMATTED)
        self.write("main.tf", FORMATTED)
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    @needs_terraform
    def test_commit_checks_unusual_file_names(self):
        self.with_terraform()
        self.write("mäin.tf", UNFORMATTED)
        self.assertEqual(self.bash("git add -A && git commit -m x", cwd=self.infra), "deny")

    @needs_terraform
    def test_commit_with_deleted_terraform_file_allowed(self):
        self.with_terraform()
        self.write("main.tf", FORMATTED)
        self.write("old.tf", FORMATTED)
        git(self.infra, "add", "-A")
        os.remove(os.path.join(self.infra, "old.tf"))
        self.assertIsNone(self.bash("git commit -am x", cwd=self.infra))

    def test_commit_with_terraform_state_or_plan_denied(self):
        for f in ("terraform.tfstate", "env/terraform.tfstate.backup", ".terraform/providers/p", "prod.tfplan"):
            self.write(f, "x")
            git(self.infra, "add", "-f", f)
            self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "deny", f)
            git(self.infra, "rm", "-q", "-r", "--cached", f)

    def test_lock_file_may_be_committed(self):
        """HashiCorp empfiehlt, die Lock-Datei zu versionieren (Provider-Versionen und Prüfsummen)."""
        self.write(".terraform.lock.hcl", "x")
        self.write("infra/.terraform.lock.hcl", "x")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    def test_new_tfvars_asks(self):
        for f in ("prod.tfvars", "env/secrets.auto.tfvars.json"):
            self.write(f, "x")
            self.assertEqual(self.bash("git add -A && git commit -m x", cwd=self.infra), "ask", f)
            os.remove(os.path.join(self.infra, f))

    def test_commit_with_ignored_state_and_tfvars_example_allowed(self):
        self.write(".gitignore", "*.tfstate\n*.tfvars\n")
        self.write("terraform.tfstate", "x")
        self.write("prod.tfvars", "x")
        self.write("prod.tfvars.example", "x")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))

    def test_unchanged_tracked_files_not_checked(self):
        """Team-Repo: was schon in HEAD liegt, hat das Projekt entschieden; ein README-Commit braucht kein terraform."""
        self.write(".terraform.lock.hcl", "x")
        self.write("env/prod.tfvars", 'location = "westeurope"\n')
        self.write("legacy.tf", UNFORMATTED)
        self.commit_all()
        self.write("README.md", "x")
        self.assertIsNone(self.bash("git add -A && git commit -m docs", cwd=self.infra))

    @needs_terraform
    def test_changed_tracked_terraform_file_checked(self):
        self.write("legacy.tf", UNFORMATTED)
        self.commit_all()
        self.with_terraform()
        self.write("legacy.tf", UNFORMATTED + 'variable "y" {}\n')
        self.assertEqual(self.bash("git commit -am x", cwd=self.infra), "deny")

    @needs_terraform
    def test_terraform_binary_inside_repo_not_run(self):
        self.write("main.tf", FORMATTED)
        self.terraform_in(".")
        self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "ask")

    @needs_terraform
    def test_terraform_from_path_below_working_dir_runs(self):
        self.write("main.tf", UNFORMATTED)
        self.terraform_in("tools")
        self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "deny")

    def test_commit_with_terraform_but_no_binary_asks(self):
        self.write("main.tf", FORMATTED)
        self.assertEqual(self.bash("git commit -m x", cwd=self.infra), "ask")

    def test_commit_without_terraform_files_needs_no_binary(self):
        self.write("README.md", "UNFORMATTED")
        self.assertIsNone(self.bash("git add -A && git commit -m x", cwd=self.infra))


class PowerShellGuardTest(unittest.TestCase):
    tearDown, decision, bash, ps = GuardTest.tearDown, GuardTest.decision, GuardTest.bash, GuardTest.ps

    def setUp(self):
        GuardTest.setUp(self)
        self.repo = make_repo(os.path.join(self.home, "dev", "Scripts"), branch="feature/x")

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

    def test_unchanged_legacy_script_not_checked(self):
        self.write("legacy/Old.ps1", "Write-Output 'Größe'\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "bestand")
        self.write("README.md", "x")
        self.assertIsNone(self.commit())

    def test_changed_legacy_script_checked(self):
        self.write("legacy/Old.ps1", "Write-Output 'Größe'\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "bestand")
        self.write("legacy/Old.ps1", "Write-Output 'Größe'\nWrite-Output 'Breite'\n")
        self.assertEqual(self.commit(), "deny")

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
        temp = os.path.join(self.base, "temp")  # Merker des Hooks
        os.makedirs(temp)
        self.env = {**{k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"},
                    "TMPDIR": temp, "TEMP": temp, "TMP": temp}

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

    def stop(self, cwd=None, background_tasks=(), active=False):
        """Hinweis an Claude (= weiterarbeiten) oder None (= darf stoppen)."""
        r = run_script(OPEN_TASKS, {"hook_event_name": "Stop", "session_id": "s1", "stop_hook_active": active,
                                    "cwd": cwd or self.repo, "background_tasks": list(background_tasks)}, self.env)
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

    def test_background_subagent_allows_stop(self):
        """Dessen Ende weckt die Session; ein Hinweis jetzt erzwänge nur Leerlauf-Runden."""
        self.write_spec([("T01", "done", [])], closing="todo")
        walker = {"id": "a1", "type": "subagent", "status": "running", "agent_type": "stefan:ui-walker"}
        self.assertIsNone(self.stop(background_tasks=[walker]))

    def test_background_shell_still_blocks_stop(self):
        """Ein Server im Hintergrund endet nie von selbst und weckt die Session nicht."""
        self.write_spec([("T01", "done", [])], closing="todo")
        server = {"id": "b1", "type": "shell", "status": "running", "command": "npm start"}
        self.assertIn("Abschluss", self.stop(background_tasks=[server]))

    def test_repeated_stop_without_progress_allowed(self):
        """Schutz vor Endlosschleifen: hat sich seit dem letzten Hinweis nichts getan, darf Claude stoppen."""
        self.write_spec([("T01", "todo", [])], closing="todo")
        self.assertIn("T01", self.stop())
        self.assertIsNone(self.stop(active=True))
        self.assertIn("T01", self.stop())  # neue Runde nach einer Nachricht des Nutzers

    def test_repeated_stop_after_progress_blocks_again(self):
        self.write_spec([("T01", "todo", []), ("T02", "todo", [])], closing="todo")
        self.assertIn("T01", self.stop())
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "x")
        self.assertIn("T01", self.stop(active=True))

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
        r = run_script(OPEN_TASKS, "kein json", self.env)
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
