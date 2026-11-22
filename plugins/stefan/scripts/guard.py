#!/usr/bin/env python3
"""PreToolUse-Hook: Schutzregeln, die nicht nur als Anweisung gelten sollen.

- pkill/killall: verboten (trifft auch Prod); lokale Server per PID auf dem Port beenden.
- Prod-Checkouts = Git-Repos direkt unter $HOME außer *-work. Sie ändert nur der Deploy:
  Edit/Write dort verboten (außer .env), Git-Änderungen verboten, andere Schreibbefehle: Rückfrage.
- Commit auf main/master verboten (außer erstem Commit und Merge-/Squash-Abschluss).
Textabgleich ist ein Sicherheitsnetz, keine Sicherheitsgrenze.
"""
import json
import os
import re
import shlex
import subprocess
import sys

MAIN = {"main", "master"}
GIT_WRITE = {"commit", "checkout", "switch", "reset", "pull", "merge", "rebase", "stash", "clean",
             "restore", "apply", "am", "cherry-pick", "revert", "rm", "mv"}
WRITE_CMDS = {"rm", "mv", "cp", "tee", "touch", "chmod", "chown", "ln", "mkdir", "rsync", "truncate", "install"}
PREFIXES = {"sudo", "nohup", "time", "command", "exec", "env"}
REDIRECTS = {">", ">>", "&>", "&>>", ">|"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&", ";;", "(", ")"}
HEREDOC = re.compile(r"(<<-?\s*(['\"]?)(\w+)\2)([^\n]*)\n.*?^[ \t]*\3[ \t]*$", re.S | re.M)


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def resolve(path, base):
    return os.path.realpath(os.path.join(base, os.path.expanduser(path)))


def prod_root(path):
    home = os.path.realpath(os.path.expanduser("~"))
    top = os.path.relpath(path, home).split(os.sep)[0]
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


def strip_prefixes(seg):
    i = 0
    while i < len(seg) and (seg[i] in PREFIXES or re.match(r"^\w+=", seg[i])):
        i += 1
    return seg[i:]


def git_call(seg, cwd):
    """(Verzeichnis, Unterbefehl, Argumente) eines git-Aufrufs, sonst None."""
    if not seg or os.path.basename(seg[0]) != "git":
        return None
    i, d = 1, cwd
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] == "-C" and i + 1 < len(seg):
            d = resolve(seg[i + 1], d)
        i += 2 if seg[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    return (d, seg[i], seg[i + 1:]) if i < len(seg) else None


def commit_on_main(d):
    if branch(d) not in MAIN or git_out(d, "rev-parse", "-q", "--verify", "HEAD") is None:
        return False  # anderer Branch oder erster Commit
    for name in ("MERGE_HEAD", "SQUASH_MSG"):
        p = git_out(d, "rev-parse", "--git-path", name)
        if p and os.path.exists(os.path.join(d, p)):
            return False  # Merge-Abschluss
    return True



def check_bash(command, cwd):
    d, ask = cwd, None
    for seg in map(strip_prefixes, segments(command)):
        if not seg:
            continue
        cmd = os.path.basename(seg[0])
        if cmd in ("pkill", "killall"):
            decide("deny", "pkill/killall trifft auch Prod-Prozesse. Lokale Server per PID auf dem Port "
                           "beenden, z. B. kill $(lsof -ti :PORT).")
        if cmd in ("cd", "pushd") and len(seg) > 1:
            d = resolve(seg[1], d)
            continue
        call = git_call(seg, d)
        if call:
            gd, sub, _ = call
            root = prod_root(gd)
            if root and sub in GIT_WRITE:
                decide("deny", f"{root} ist ein Prod-Checkout, den nur der Deploy aktualisiert.")
            if sub == "commit" and commit_on_main(gd):
                decide("deny", "Nie direkt auf main committen: erst Branch anlegen (git switch -c feat/…), "
                               "die Änderungen wandern mit.")
            continue
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
    try:
        data = json.load(sys.stdin)
    except ValueError:
        return
    if not isinstance(data, dict):
        return
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    if data.get("tool_name") == "Bash":
        check_bash(tool_input.get("command", ""), cwd)
    elif tool_input.get("file_path") or tool_input.get("notebook_path"):
        check_edit(tool_input.get("file_path") or tool_input.get("notebook_path"), cwd)


if __name__ == "__main__":
    main()
