#!/usr/bin/env python3
"""PreToolUse-Hook (Bash, PowerShell): Schutzregeln, die nicht nur als Anweisung gelten sollen.

- Prozesse nach Namen beenden (pkill, killall, kill mit pgrep/pidof, Stop-Process ohne Id, taskkill ohne /PID):
  verboten; lokale Server per PID auf dem Port beenden.
- Commit auf main/master verboten (außer erstem Commit und Merge-/Squash-Abschluss); ein Branchwechsel vorher im
  selben Befehl zählt.
- Commit mit Co-Authored-By-Trailer verboten (Vorgabe des Nutzers), auch aus einer Nachrichtendatei (-F).
- Commit-Prüfungen nur für neue und geänderte Dateien; was unverändert in HEAD liegt, hat das Projekt entschieden:
  - Terraform: neue State-, Plan-, Lock- und .terraform/-Dateien verboten (gehören in .gitignore), *.tfvars erlaubt;
    geänderte Terraform-Dateien müssen `terraform fmt -check` bestehen.
  - PowerShell: Skripte (.ps1/.psm1/.psd1) mit Nicht-ASCII ohne BOM verboten, außer per `#Requires -Version 6+`
    bzw. `-PSEdition Core` auf PowerShell 7 beschränkt (5.1 liest sie sonst als ANSI).
- Terraform-Befehle, die Infrastruktur oder State ändern (apply, destroy, import, refresh, state rm/mv …,
  init -migrate-state): Rückfrage, ebenso `terraform test` mit run-Blöcken ohne eigenes `command = plan` in
  Testdateien (HCL, JSON) ohne `mock_provider`; Testdateien über 1 MiB gelten als nicht prüfbar.
Prod-Checkouts auf dem Homelab schützt das Plugin stefan-homelab.
Textabgleich ist ein Sicherheitsnetz, keine Sicherheitsgrenze.
"""
import json
import os
import re
import shutil
import subprocess
import sys

from shellparse import command_name, commands, git_call, resolve

MAIN = {"main", "master"}
KILL_BY_NAME = ("Prozesse nicht nach Namen beenden (auch nicht per pgrep/pidof), das trifft auch fremde Prozesse wie "
                "Prod. Lokale Server per PID auf dem Port beenden: kill $(lsof -ti :PORT) bzw. "
                "Stop-Process -Id (Get-NetTCPConnection -LocalPort PORT).OwningProcess.")
PID_LOOKUP = {"pgrep", "pidof"}
STOP_PROCESS = {"stop-process", "spps"}
GET_PROCESS = {"get-process", "gps", "ps"}
PID_ARG = re.compile(r"^(?:\d+|\$[\w:.]+)(?:,(?:\d+|\$[\w:.]+))*$")  # 4711, 4711,4712, $p.Id
CO_AUTHOR = re.compile(r"co-authored-by\s*[:=]", re.I)
MESSAGE_MAX = 1 << 16
CREATE_FLAGS = {"-b", "-B", "-c", "-C", "--create", "--force-create", "--orphan"}
TF_CHANGE = {"apply", "destroy", "import", "refresh", "taint", "untaint", "force-unlock"}
TF_STATE_READ = {"list", "show", "pull", "identities"}
TF_STATE_MIGRATE = {"migrate-state", "force-copy"}
TF_FILES = (".tf", ".tftest.hcl")
TF_TEST_SUFFIXES = (".tftest.hcl", ".tftest.json")
TF_TEST_MAX = 1 << 20  # größere Testdateien gelten als nicht prüfbar
# Zeichenketten (Klammern darin zählen nicht) und Kommentare in HCL
TF_TEST_NOISE = re.compile(r'"(?:\\.|[^"\\\n])*"|/\*.*?\*/|(?:#|//)[^\n]*', re.S)
TF_TOKENS = re.compile(r'(?P<run>\brun(?:\s*""|\s+[A-Za-z_][\w-]*)\s*\{)|(?P<plan>\bcommand\s*=\s*plan\b)'
                       r'|(?P<open>\{)|(?P<close>\})')
PS_SUFFIXES = (".ps1", ".psm1", ".psd1")
PS_BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")
PS_CORE_ONLY = re.compile(rb"^[ \t]*#requires\b[^\n]*?-(?:version[ \t]+([0-9]+)|psedition[ \t]+core)", re.I | re.M)


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def git_out(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def branch(d):
    return git_out(d, "symbolic-ref", "--short", "-q", "HEAD")


def selects_by_id(args):
    return any(a.lower().split(":")[0] in ("-id", "-i") for a in args)


def stop_process_by_name(args, piped_from):
    """True, wenn Stop-Process (spps, kill) nicht nachweislich Prozess-Ids beendet."""
    if any(a.lower().startswith(("-n", "-in")) for a in args):
        return True  # -Name, -InputObject
    if selects_by_id(args) or any(PID_ARG.match(a) for a in args):
        return False  # -Id oder Ids als erstes Argument
    return not (piped_from and command_name(piped_from[0]) in GET_PROCESS and selects_by_id(piped_from[1:]))


def kills_by_name(name, args, powershell, piped_from):
    if name in ("pkill", "killall"):
        return True
    if name in STOP_PROCESS or (powershell and name == "kill"):
        return stop_process_by_name(args, piped_from)
    return name == "taskkill" and "/pid" not in [a.lower() for a in args]


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
    flags = {a.lstrip("-").split("=")[0] for a in seg[1:] if a.startswith("-")}
    return (sub in TF_CHANGE or (sub == "state" and bool(rest) and rest[0] not in TF_STATE_READ)
            or (sub == "workspace" and rest[:1] == ["delete"]) or (sub == "init" and bool(flags & TF_STATE_MIGRATE)))


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


def unique_json_object(pairs):
    """object_pairs_hook: doppelte Schlüssel (in HCL-JSON ggf. mehrere Blöcke) nicht stillschweigend überschreiben."""
    if len({k for k, _ in pairs}) != len(pairs):
        raise ValueError("doppelter Schlüssel")
    return dict(pairs)


def json_runs_real_infrastructure(text):
    """Wie runs_real_infrastructure, für Testdateien in JSON-Syntax."""
    try:
        doc = json.loads(text, object_pairs_hook=unique_json_object)
    except (ValueError, RecursionError):  # ungültig, doppelte Schlüssel, zu tief: nicht prüfbar
        return True
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
                data.decode("utf-8-sig", errors="replace")):
            bad.append(f)
    if bad:
        return (f"terraform test kann echte Infrastruktur anlegen: run-Blöcke ohne `command = plan` und ohne "
                f"`mock_provider` in {', '.join(bad[:5])}. Nur mit Freigabe, nie gegen Prod.")
    return None


def commit_candidates(top):
    """(neu, geändert): Dateien, die der Commit neu bzw. geändert enthalten kann – Index, Arbeitsbaum, ungetrackt
    und nicht ignoriert (so zählt auch ein `git add -A` im selben Befehl); gelöschte zählen nicht. Was unverändert
    in HEAD liegt, hat das Projekt entschieden und wird nicht geprüft. Ohne HEAD (erster Commit) ist alles neu."""
    def names(*args):
        out = subprocess.run(["git", "-C", top, *args], capture_output=True).stdout
        return [f for f in os.fsdecode(out).split("\0") if f]

    new = set(names("ls-files", "-z", "--others", "--exclude-standard"))
    if git_out(top, "rev-parse", "-q", "--verify", "HEAD") is None:
        new.update(names("ls-files", "-z", "--cached"))
        return new, set(new)
    changed = set(new)
    for staged in (["--cached"], []):
        fields = names("diff", "-z", "--name-status", "--no-renames", *staged, "HEAD")
        for status, path in zip(fields[::2], fields[1::2]):
            if status != "D":
                changed.add(path)
            if status == "A":
                new.add(path)
    return new, changed


def is_tf_artifact(path):
    """State, Plan, Lock-Datei oder Inhalt von .terraform/ (Pfad relativ zum Repo, mit /)."""
    *dirs, name = path.split("/")
    return (".terraform" in dirs or name.endswith((".tfstate", ".tfplan")) or ".tfstate." in name
            or name == ".terraform.lock.hcl")


def terraform_fmt_problem(d, top, files):
    """(Entscheidung, Grund), wenn geänderte Terraform-Dateien `terraform fmt -check` nicht bestehen oder das nicht
    prüfbar ist, sonst None."""
    if not files:
        return None
    exe = shutil.which("terraform")
    if not exe:
        return "ask", "Geänderte Terraform-Dateien, aber terraform fehlt: fmt vor dem Commit nicht prüfbar."

    def norm(p):
        return os.path.normcase(os.path.realpath(p))
    if norm(os.path.dirname(os.path.abspath(exe))) in (norm(d), norm(os.getcwd())):  # Windows sucht dort zuerst
        return "ask", f"terraform liegt im Arbeitsordner ({exe}): fmt-Prüfung nicht ausgeführt."
    if os.path.splitext(exe)[1].lower() in (".bat", ".cmd"):  # cmd.exe deutete Sonderzeichen in Dateinamen
        return "ask", f"terraform ist ein Batch-Wrapper ({exe}): fmt-Prüfung nicht ausgeführt."
    try:
        r = subprocess.run([exe, "fmt", "-check", "--", *files], cwd=top, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=8)
    except subprocess.TimeoutExpired:
        return "ask", "terraform fmt -check hat nicht rechtzeitig geantwortet."
    if r.returncode != 0:
        return "deny", ("Vor jedem Commit terraform fmt: die betroffenen Dateien mit `terraform fmt <datei>` "
                        f"formatieren, stagen, Commit wiederholen. Betroffen: {(r.stdout + r.stderr).strip()}")
    return None


def terraform_commit_problem(d, top, new, changed):
    """(Entscheidung, Grund), wenn der Commit Terraform-Artefakte oder unformatiertes Terraform enthielte, sonst
    None."""
    artifacts = sorted(f for f in new if is_tf_artifact(f))
    if artifacts:
        return "deny", (f"State, Plan, Lock-Datei und .terraform/ gehören nicht ins Repo: {', '.join(artifacts[:5])}. Mit "
                        "`git rm --cached` aus dem Index nehmen und in .gitignore eintragen.")
    return terraform_fmt_problem(d, top, sorted(f for f in changed
                                                if f.endswith(TF_FILES) and os.path.isfile(os.path.join(top, f))))


def powershell_commit_problem(top, changed):
    """Grund, wenn der Commit PowerShell-Skripte enthielte, die Windows PowerShell 5.1 falsch dekodiert, sonst None."""
    bad = []
    for f in sorted(changed):
        if not f.lower().endswith(PS_SUFFIXES):
            continue
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


def message_files(args):
    """Nachrichtendateien von git commit (-F, --file); `-` liest den Heredoc aus dem Befehl selbst."""
    files = flag_values(args, "--file")
    for i, a in enumerate(args):
        m = re.match(r"^-[a-zA-Z]*F(.*)$", a)
        if m and not a.startswith("--"):
            files.append(m.group(1) or (args[i + 1] if i + 1 < len(args) else "-"))
    return [f for f in files if f != "-"]


def read_text(path):
    try:
        with open(path, "rb") as f:
            return f.read(MESSAGE_MAX).decode("utf-8", errors="replace")
    except OSError:  # fehlt oder nicht lesbar: git meldet das selbst
        return ""


def commit_problem(command, d, args, switched):
    """(Entscheidung, Grund) für git commit im Verzeichnis d, sonst None."""
    if any(CO_AUTHOR.search(t) for t in [command] + [read_text(resolve(f, d)) for f in message_files(args)]):
        return "deny", ("Ohne Co-Authored-By committen (Vorgabe des Nutzers): denselben Commit ohne diese Zeile "
                        "wiederholen.")
    if switched[d] in MAIN if d in switched else commit_on_main(d):
        return "deny", ("Nie direkt auf main committen: erst einen Branch nach dem Schema des Projekts anlegen "
                        "(sonst feature/… bzw. fix/…), die Änderungen wandern mit.")
    top = git_out(d, "rev-parse", "--show-toplevel")
    if not top:
        return None
    new, changed = commit_candidates(top)
    ps = powershell_commit_problem(top, changed)
    return ("deny", ps) if ps else terraform_commit_problem(d, top, new, changed)


def check_shell(command, cwd, powershell=False):
    ask, switched, prev, lookup, kill = None, {}, None, False, False
    for name, seg, sep, d in commands(command, cwd, powershell):
        piped_from, prev = (prev if sep in ("|", "|&") else None), seg
        if kills_by_name(name, seg[1:], powershell, piped_from):
            decide("deny", KILL_BY_NAME)
        lookup = lookup or any(command_name(t.lstrip("`$(")) in PID_LOOKUP for t in seg)
        kill = kill or name == "kill" or (name == "xargs" and "kill" in map(command_name, seg[1:]))
        call = git_call(seg, d)
        if call:
            gd, sub, args = call
            if sub in ("checkout", "switch") and switch_target(sub, args):
                switched[gd] = switch_target(sub, args)
            if sub == "commit":
                problem = commit_problem(command, gd, args, switched)
                if problem and problem[0] == "deny":
                    decide(*problem)
                ask = ask or (problem and problem[1])
            continue
        if name == "terraform" and not ask:
            ask = ("terraform ändert Infrastruktur bzw. State: nur nach geprüftem Plan und nie gegen Prod ohne Freigabe."
                   if terraform_changes(seg) else terraform_test_problem(seg, d))
    if lookup and kill:  # kill $(pgrep …), pgrep … | xargs kill
        decide("deny", KILL_BY_NAME)
    if ask:
        decide("ask", ask)


def main():
    try:  # UTF-8 auch unter Windows, wo die Standardkodierung abweicht
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except ValueError:
        return
    if isinstance(data, dict) and data.get("tool_name") in ("Bash", "PowerShell"):
        command = (data.get("tool_input") or {}).get("command", "")
        check_shell(command, data.get("cwd") or os.getcwd(), data.get("tool_name") == "PowerShell")


if __name__ == "__main__":
    main()
