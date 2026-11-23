#!/usr/bin/env python3
"""PreToolUse-Hook: Schutzregeln, die nicht nur als Anweisung gelten sollen.

- Prozesse nach Namen beenden (pkill, killall, Stop-Process ohne -Id, taskkill ohne /PID): verboten
  (trifft auch Prod); lokale Server per PID auf dem Port beenden.
- Prod-Checkouts = Git-Repos direkt unter $HOME außer *-work. Sie ändert nur der Deploy:
  Edit/Write dort verboten (außer .env), Git-Änderungen verboten, andere Schreibbefehle: Rückfrage.
- Commit auf main/master verboten (außer erstem Commit und Merge-/Squash-Abschluss); ein Branchwechsel
  vorher im selben Befehl zählt.
- Commit mit Co-Authored-By-Trailer verboten (Vorgabe des Nutzers).
- Terraform: Commit nur, wenn `terraform fmt -check` für die von git erfassten Terraform-Dateien durchläuft; Befehle, die
  Infrastruktur oder State ändern (apply, destroy, import, state rm/mv …): Rückfrage.
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


def terraform_unformatted(d):
    """Grund zum Ablehnen bzw. Nachfragen, wenn ein Commit unformatiertes Terraform enthielte, sonst None."""
    top = git_out(d, "rev-parse", "--show-toplevel")
    listed = git_out(top, "ls-files", "--cached", "--others", "--exclude-standard", "--",
                     "*.tf", "*.tfvars", "*.tftest.hcl") if top else None
    files = [f for f in (listed or "").splitlines() if os.path.exists(os.path.join(top, f))]
    if not files:
        return None
    exe = shutil.which("terraform")
    if not exe:
        return "ask", "Das Repo enthält Terraform, aber terraform fehlt: fmt vor dem Commit nicht prüfbar."
    try:  # nur von git erfasste Dateien, nicht .terraform/ oder andere ignorierte Ordner
        r = subprocess.run([exe, "fmt", "-check", *files], cwd=top, capture_output=True, text=True, timeout=8)
    except subprocess.TimeoutExpired:
        return "ask", "terraform fmt -check hat nicht rechtzeitig geantwortet."
    if r.returncode != 0:
        return "deny", ("Vor jedem Commit terraform fmt: die betroffenen Dateien mit `terraform fmt <datei>` "
                        f"formatieren, stagen, Commit wiederholen. Betroffen: {(r.stdout + r.stderr).strip()}")
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
                fmt = terraform_unformatted(gd)
                if fmt and fmt[0] == "deny":
                    decide(*fmt)
                ask = ask or (fmt and fmt[1])
            continue
        if cmd == "terraform" and terraform_changes(seg) and not ask:
            ask = "terraform ändert Infrastruktur bzw. State: nur nach geprüftem Plan und nie gegen Prod ohne Freigabe."
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
