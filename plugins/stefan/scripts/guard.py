#!/usr/bin/env python3
"""PreToolUse-Hook: Schutzregeln, die nicht nur als Anweisung gelten sollen.

- Prozesse nach Namen beenden (pkill, killall, Stop-Process ohne -Id, taskkill ohne /PID): verboten
  (trifft auch Prod); lokale Server per PID auf dem Port beenden.
- Prod-Checkouts = Git-Repos direkt unter $HOME außer *-work. Sie ändert nur der Deploy:
  Edit/Write dort verboten (außer .env), Git-Änderungen verboten, andere Schreibbefehle: Rückfrage.
- Commit auf main/master verboten (außer erstem Commit und Merge-/Squash-Abschluss); ein Branchwechsel
  vorher im selben Befehl zählt.
- Commit mit Co-Authored-By-Trailer verboten (Vorgabe des Nutzers).
- Terraform: Commit mit State, Plan, `.terraform/`, Lock-Datei oder `*.tfvars` verboten; Commit nur, wenn `terraform fmt -check` für die von git erfassten Terraform-Dateien durchläuft; Befehle, die
  Infrastruktur oder State ändern (apply, destroy, import, state rm/mv …): Rückfrage, ebenso `terraform test` mit
  run-Blöcken ohne eigenes `command = plan` in Testdateien (HCL, JSON) ohne `mock_provider`; Testdateien über 1 MiB
  gelten als nicht prüfbar.
- PowerShell: Commit verboten, wenn ein Skript (.ps1/.psm1/.psd1) Nicht-ASCII ohne BOM enthält und nicht per
  `#Requires -Version 6+` bzw. `-PSEdition Core` auf PowerShell 7 beschränkt ist (5.1 liest es sonst als ANSI).
Gilt für Bash (Linux, Git Bash unter Windows) und PowerShell.
Textabgleich ist ein Sicherheitsnetz, keine Sicherheitsgrenze.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

MAIN = {"main", "master"}
GIT_WRITE = {"commit", "checkout", "switch", "reset", "pull", "merge", "rebase", "stash", "clean",
             "restore", "apply", "am", "cherry-pick", "revert", "rm", "mv"}
WRITE_CMDS = {"rm", "mv", "cp", "tee", "touch", "chmod", "chown", "ln", "mkdir", "rsync", "truncate", "install",
              # PowerShell (Kleinschreibung) inkl. Aliasse
              "set-content", "add-content", "clear-content", "out-file", "new-item", "remove-item", "copy-item",
              "move-item", "rename-item", "sc", "ac", "ni", "ri", "del", "erase", "rd", "rmdir", "cpi", "copy",
              "mi", "move", "rni", "ren"}
CD_CMDS = {"cd", "pushd", "set-location", "sl", "chdir", "push-location"}
KILL_BY_NAME = "Prozesse nicht nach Namen beenden, das trifft auch Prod. Lokale Server per PID auf dem Port beenden: " \
               "kill $(lsof -ti :PORT) bzw. Stop-Process -Id (Get-NetTCPConnection -LocalPort PORT).OwningProcess."
PREFIXES = {"sudo", "nohup", "time", "command", "exec", "env"}
REDIRECTS = {">", ">>", "&>", "&>>", ">|"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&", ";;", "(", ")"}
CO_AUTHOR = re.compile(r"co-authored-by\s*[:=]", re.I)
CREATE_FLAGS = {"-b", "-B", "-c", "-C", "--create", "--force-create", "--orphan"}
TF_CHANGE = {"apply", "destroy", "import", "taint", "untaint", "force-unlock"}
TF_STATE_READ = {"list", "show", "pull", "identities"}
TF_FORBIDDEN = ["**/*.tfstate", "**/*.tfstate.*", "**/.terraform/**", "**/.terraform.lock.hcl", "**/*.tfplan",
                "**/*.tfvars", "**/*.tfvars.json"]
TF_TEST_SUFFIXES = (".tftest.hcl", ".tftest.json")
TF_TEST_MAX = 1 << 20  # größere Testdateien gelten als nicht prüfbar
# Zeichenketten (Klammern darin zählen nicht) und Kommentare in HCL
TF_TEST_NOISE = re.compile(r'"(?:\\.|[^"\\\n])*"|/\*.*?\*/|(?:#|//)[^\n]*', re.S)
TF_TOKENS = re.compile(r'(?P<run>\brun(?:\s*""|\s+[A-Za-z_][\w-]*)\s*\{)|(?P<plan>\bcommand\s*=\s*plan\b)'
                       r'|(?P<open>\{)|(?P<close>\})')
PS_FILES = ["**/*.ps1", "**/*.psm1", "**/*.psd1"]
PS_BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")
PS_CORE_ONLY = re.compile(rb"^[ \t]*#requires\b[^\n]*?-(?:version[ \t]+([0-9]+)|psedition[ \t]+core)", re.I | re.M)
HEREDOC = re.compile(r"(<<-?\s*(['\"]?)(\w+)\2)([^\n]*)\n.*?^[ \t]*\3[ \t]*$", re.S | re.M)


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def resolve(path, base):
    m = re.match(r"^/([a-zA-Z])(/|$)", path) if os.name == "nt" else None
    if m:  # Git-Bash-Pfad /c/... → C:/...
        path = f"{m.group(1)}:/{path[3:]}"
    return os.path.realpath(os.path.join(base, os.path.expanduser(path)))


def prod_root(path):
    home = os.path.realpath(os.path.expanduser("~"))
    try:
        top = os.path.relpath(path, home).split(os.sep)[0]
    except ValueError:  # anderes Laufwerk
        return None
    if top in (".", "..") or top.startswith(".") or top.endswith("-work"):
        return None
    root = os.path.join(home, top)
    return root if os.path.exists(os.path.join(root, ".git")) else None


def git_out(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def branch(d):
    return git_out(d, "symbolic-ref", "--short", "-q", "HEAD")


def segments(command):
    """Einfache Befehle als Token-Listen; Heredoc-Inhalte zählen nicht als Befehle."""
    command = HEREDOC.sub(r"\1\4", command.replace("\\\n", " "))
    try:
        lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:  # unvollständige Quotes: grob zerlegen
        return [s.split() for s in re.split(r"&&|\|\||[;|&()\n]", command)]
    result, seg = [], []
    for tok in tokens:
        if tok in SEPARATORS:
            result.append(seg)
            seg = []
        else:
            seg.append(tok)
    return result + [seg]


def command_name(word):
    name = os.path.basename(word.replace("\\", "/")).lower()
    return name[:-4] if name.endswith(".exe") else name


def kills_by_name(cmd, args, powershell):
    if cmd in ("pkill", "killall"):
        return True
    lower = [a.lower() for a in args]
    if cmd in ("stop-process", "spps") or (powershell and cmd == "kill" and any(a.startswith("-n") or a.startswith("-p") for a in lower)):
        return not any(a in ("-id", "-i") for a in lower)
    return cmd == "taskkill" and "/pid" not in lower


def strip_prefixes(seg):
    i = 0
    while i < len(seg) and (seg[i] in PREFIXES or re.match(r"^\w+=", seg[i])):
        i += 1
    return seg[i:]


def git_call(seg, cwd):
    """(Verzeichnis, Unterbefehl, Argumente) eines git-Aufrufs, sonst None."""
    if not seg or command_name(seg[0]) != "git":
        return None
    i, d = 1, cwd
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] == "-C" and i + 1 < len(seg):
            d = resolve(seg[i + 1], d)
        i += 2 if seg[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    return (d, seg[i], seg[i + 1:]) if i < len(seg) else None


def switch_target(sub, args):
    """Branch, auf den checkout/switch wechselt; None, wenn unklar (z. B. checkout einer Datei)."""
    for i, a in enumerate(args):
        if a in CREATE_FLAGS:
            return args[i + 1] if i + 1 < len(args) else None
    names = [a for a in args if not a.startswith("-")]
    if "--" in args or not names:
        return None
    if sub == "switch" or names[0] in MAIN:
        return names[0]
    return None


def commit_on_main(d):
    if branch(d) not in MAIN or git_out(d, "rev-parse", "-q", "--verify", "HEAD") is None:
        return False  # anderer Branch oder erster Commit
    for name in ("MERGE_HEAD", "SQUASH_MSG"):
        p = git_out(d, "rev-parse", "--git-path", name)
        if p and os.path.exists(os.path.join(d, p)):
            return False  # Merge-Abschluss
    return True


def terraform_changes(seg):
    """True, wenn ein terraform-Aufruf Infrastruktur oder State ändert."""
    args = [a for a in seg[1:] if not a.startswith("-")]
    if not args:
        return False
    sub, rest = args[0], args[1:]
    return (sub in TF_CHANGE or (sub == "state" and bool(rest) and rest[0] not in TF_STATE_READ)
            or (sub == "workspace" and rest[:1] == ["delete"]))


def flag_values(args, name):
    """Werte einer Option als `name=wert` oder `name wert`."""
    vals = []
    for i, a in enumerate(args):
        if a.startswith(name + "="):
            vals.append(a[len(name) + 1:])
        elif a == name and i + 1 < len(args):
            vals.append(args[i + 1])
    return vals


def runs_real_infrastructure(text):
    """True, wenn eine HCL-Testdatei ohne mock_provider einen run-Block ohne eigenes `command = plan` hat."""
    code = TF_TEST_NOISE.sub(lambda m: '""' if m.group(0).startswith('"') else "", text)
    if re.search(r"\bmock_provider\b", code):
        return False
    depth, in_run, planned = 0, False, False
    for t in TF_TOKENS.finditer(code):  # ein Durchlauf über die Datei
        kind = t.lastgroup
        if kind == "run" and depth == 0:
            depth, in_run, planned = 1, True, False
        elif kind in ("run", "open"):
            depth += 1
        elif kind == "close":
            depth = max(depth - 1, 0)
            if depth == 0 and in_run:
                if not planned:
                    return True
                in_run = False
        elif kind == "plan" and in_run and depth == 1:  # nur direkt im run-Block, nicht in Unterblöcken
            planned = True
    return in_run and not planned


def json_runs_real_infrastructure(text):
    """Wie runs_real_infrastructure, für Testdateien in JSON-Syntax."""
    try:
        doc = json.loads(text)
    except RecursionError:  # zu tief verschachtelt: nicht prüfbar
        return True
    except ValueError:  # ungültig: terraform führt sie nicht aus
        return False
    if not isinstance(doc, dict) or "mock_provider" in doc:
        return False
    runs, bodies = doc.get("run"), []
    for group in runs if isinstance(runs, list) else [runs]:
        if isinstance(group, dict):  # Label → Block bzw. Liste von Blöcken
            for body in group.values():
                bodies += body if isinstance(body, list) else [body]
    return any(not (isinstance(b, dict) and b.get("command") == "plan") for b in bodies)


def terraform_test_problem(seg, cwd):
    """Grund für eine Rückfrage, wenn `terraform test` Testdateien ausführt, die echte Infrastruktur anlegen."""
    args = seg[1:]
    if [a for a in args if not a.startswith("-")][:1] != ["test"]:
        return None
    base = resolve(flag_values(args, "-chdir")[-1], cwd) if flag_values(args, "-chdir") else cwd
    files = flag_values(args, "-filter")
    if not files:
        for sub in ("", (flag_values(args, "-test-directory") or ["tests"])[-1]):
            try:
                files += [os.path.join(sub, f) for f in sorted(os.listdir(os.path.join(base, sub)))
                          if f.endswith(TF_TEST_SUFFIXES)]
            except OSError:  # Ordner fehlt
                pass
    bad = []
    for f in files:
        path = os.path.join(base, f)
        if not os.path.isfile(path):  # Ordner, Gerät, FIFO: nicht öffnen
            continue
        try:
            with open(path, "rb") as fh:
                data = fh.read(TF_TEST_MAX + 1)
        except OSError:  # gelöscht oder nicht lesbar
            continue
        if len(data) > TF_TEST_MAX:
            bad.append(f"{f} (zu groß zum Prüfen)")
        elif (json_runs_real_infrastructure if f.endswith(".json") else runs_real_infrastructure)(
                data.decode("utf-8", errors="replace")):
            bad.append(f)
    if bad:
        return (f"terraform test kann echte Infrastruktur anlegen: run-Blöcke ohne `command = plan` und ohne "
                f"`mock_provider` in {', '.join(bad[:5])}. Nur mit Freigabe, nie gegen Prod.")
    return None


def repo_files(top, *patterns):
    """Dateien im Index oder ungetrackt und nicht ignoriert, die auf ein Glob-Muster passen."""
    out = subprocess.run(["git", "-C", top, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
                          *(f":(glob){p}" for p in patterns)], capture_output=True).stdout
    return sorted(set(f for f in os.fsdecode(out).split("\0") if f))


def terraform_commit_problem(d):
    """(Entscheidung, Grund), wenn ein Commit Terraform-Secrets bzw. unformatiertes Terraform enthielte, sonst None."""
    top = git_out(d, "rev-parse", "--show-toplevel")
    if not top:
        return None
    forbidden = repo_files(top, *TF_FORBIDDEN)
    if forbidden:
        return "deny", ("State, Plan, .terraform/, Lock-Datei und *.tfvars gehören nicht ins Repo: "
                        f"{', '.join(forbidden[:5])}. Mit `git rm --cached` aus dem Index nehmen und in .gitignore "
                        "eintragen; Beispielwerte als *.tfvars.example.")
    files = [f for f in repo_files(top, "**/*.tf", "**/*.tftest.hcl") if os.path.exists(os.path.join(top, f))]
    if not files:
        return None
    exe = shutil.which("terraform")
    if not exe:
        return "ask", "Das Repo enthält Terraform, aber terraform fehlt: fmt vor dem Commit nicht prüfbar."
    def norm(p):
        return os.path.normcase(os.path.realpath(p))
    if norm(os.path.dirname(os.path.abspath(exe))) in (norm(d), norm(os.getcwd())):  # Windows sucht dort zuerst
        return "ask", f"terraform liegt im Arbeitsordner ({exe}): fmt-Prüfung nicht ausgeführt."
    if os.path.splitext(exe)[1].lower() in (".bat", ".cmd"):  # cmd.exe deutete Sonderzeichen in Dateinamen
        return "ask", f"terraform ist ein Batch-Wrapper ({exe}): fmt-Prüfung nicht ausgeführt."
    try:  # nur von git erfasste Dateien, nicht .terraform/ oder andere ignorierte Ordner
        r = subprocess.run([exe, "fmt", "-check", "--", *files], cwd=top, capture_output=True, text=True, timeout=8)
    except subprocess.TimeoutExpired:
        return "ask", "terraform fmt -check hat nicht rechtzeitig geantwortet."
    if r.returncode != 0:
        return "deny", ("Vor jedem Commit terraform fmt: die betroffenen Dateien mit `terraform fmt <datei>` "
                        f"formatieren, stagen, Commit wiederholen. Betroffen: {(r.stdout + r.stderr).strip()}")
    return None


def powershell_commit_problem(d):
    """Grund, wenn ein Commit PowerShell-Skripte enthielte, die Windows PowerShell 5.1 falsch dekodiert, sonst None."""
    top = git_out(d, "rev-parse", "--show-toplevel")
    if not top:
        return None
    bad = []
    for f in repo_files(top, *PS_FILES):
        try:
            with open(os.path.join(top, f), "rb") as fh:
                data = fh.read()
        except OSError:  # gelöscht oder nicht lesbar
            continue
        if data.isascii() or data.startswith(PS_BOMS):
            continue
        m = PS_CORE_ONLY.search(data)
        if m and (m.group(1) is None or int(m.group(1)) >= 6):
            continue
        bad.append(f)
    if bad:
        return (f"PowerShell-Skripte mit Nicht-ASCII ohne BOM: {', '.join(bad[:5])}. Windows PowerShell 5.1 liest "
                "sie als ANSI. Als UTF-8 mit BOM speichern, auf ASCII umstellen oder mit `#Requires -Version 7.2` "
                "auf PowerShell 7 beschränken.")
    return None


def check_shell(command, cwd, powershell=False):
    if powershell:  # Backslash ist dort Pfadtrenner, kein Escape
        command = command.replace("\\", "/")
    d, ask, switched = cwd, None, {}
    for seg in map(strip_prefixes, segments(command)):
        if not seg:
            continue
        cmd = command_name(seg[0])
        if kills_by_name(cmd, seg[1:], powershell):
            decide("deny", KILL_BY_NAME)
        if cmd in CD_CMDS and len(seg) > 1:
            d = resolve(next((a for a in seg[1:] if not a.startswith("-")), "."), d)
            continue
        call = git_call(seg, d)
        if call:
            gd, sub, args = call
            root = prod_root(gd)
            if root and sub in GIT_WRITE:
                decide("deny", f"{root} ist ein Prod-Checkout, den nur der Deploy aktualisiert.")
            if sub in ("checkout", "switch") and switch_target(sub, args):
                switched[gd] = switch_target(sub, args)
            if sub == "commit" and CO_AUTHOR.search(command):
                decide("deny", "Ohne Co-Authored-By committen (Vorgabe des Nutzers): denselben Commit ohne diese "
                               "Zeile wiederholen.")
            if sub == "commit" and (switched[gd] in MAIN if gd in switched else commit_on_main(gd)):
                decide("deny", "Nie direkt auf main committen: erst einen Branch nach dem Schema des Projekts anlegen "
                               "(sonst feat/… bzw. fix/…), die Änderungen wandern mit.")
            if sub == "commit":
                fmt = terraform_commit_problem(gd)
                if fmt and fmt[0] == "deny":
                    decide(*fmt)
                ask = ask or (fmt and fmt[1])
                ps = powershell_commit_problem(gd)
                if ps:
                    decide("deny", ps)
            continue
        if cmd == "terraform" and not ask:
            ask = ("terraform ändert Infrastruktur bzw. State: nur nach geprüftem Plan und nie gegen Prod ohne Freigabe."
                   if terraform_changes(seg) else terraform_test_problem(seg, d))
        targets = [seg[i + 1] for i in range(len(seg) - 1) if seg[i] in REDIRECTS]
        if cmd in WRITE_CMDS or (cmd == "sed" and any(t.startswith("-i") for t in seg[1:])):
            targets += [t for t in seg[1:] if not t.startswith("-")]
        root = next(filter(None, (prod_root(resolve(t, d)) for t in targets)), None)
        if root and not ask:
            ask = f"Schreibzugriff in den Prod-Checkout {root}, den sonst nur der Deploy ändert."
    if ask:
        decide("ask", ask)


def check_edit(path, cwd):
    p = resolve(path, cwd)
    root = prod_root(p)
    if root and os.path.basename(p) != ".env":
        decide("deny", f"{root} ist ein Prod-Checkout, den nur der Deploy aktualisiert (nur .env ist erlaubt).")


def main():
    try:  # UTF-8 auch unter Windows, wo die Standardkodierung abweicht
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except ValueError:
        return
    if not isinstance(data, dict):
        return
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    if data.get("tool_name") in ("Bash", "PowerShell"):
        check_shell(tool_input.get("command", ""), cwd, data.get("tool_name") == "PowerShell")
    elif tool_input.get("file_path") or tool_input.get("notebook_path"):
        check_edit(tool_input.get("file_path") or tool_input.get("notebook_path"), cwd)


if __name__ == "__main__":
    main()
