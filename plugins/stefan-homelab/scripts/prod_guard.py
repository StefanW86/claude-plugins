#!/usr/bin/env python3
"""PreToolUse-Hook des Homelabs: Prod-Checkouts ändert nur der Deploy.

Prod-Checkout = Git-Repo direkt unter $HOME, außer *-work und Punktordnern. Edit/Write dort verboten (außer .env),
Git-Änderungen verboten, andere Schreibbefehle in Bash bzw. PowerShell: Rückfrage.
Textabgleich ist ein Sicherheitsnetz, keine Sicherheitsgrenze.
"""
import json
import os
import sys

from shellparse import commands, git_call, resolve

GIT_WRITE = {"commit", "checkout", "switch", "reset", "pull", "merge", "rebase", "stash", "clean",
             "restore", "apply", "am", "cherry-pick", "revert", "rm", "mv"}
WRITE_CMDS = {"rm", "mv", "cp", "tee", "touch", "chmod", "chown", "ln", "mkdir", "rsync", "truncate", "install",
              # PowerShell (Kleinschreibung) inkl. Aliasse
              "set-content", "add-content", "clear-content", "out-file", "new-item", "remove-item", "copy-item",
              "move-item", "rename-item", "sc", "ac", "ni", "ri", "del", "erase", "rd", "rmdir", "cpi", "copy",
              "mi", "move", "rni", "ren"}
REDIRECTS = {">", ">>", "&>", "&>>", ">|"}


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


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


def check_shell(command, cwd, powershell=False):
    ask = None
    for name, seg, _, d in commands(command, cwd, powershell):
        call = git_call(seg, d)
        if call:
            root = prod_root(call[0])
            if root and call[1] in GIT_WRITE:
                decide("deny", f"{root} ist ein Prod-Checkout, den nur der Deploy aktualisiert.")
            continue
        targets = [seg[i + 1] for i in range(len(seg) - 1) if seg[i] in REDIRECTS]
        if name in WRITE_CMDS or (name == "sed" and any(t.startswith("-i") for t in seg[1:])):
            targets += [t for t in seg[1:] if not t.startswith("-")]
        root = next(filter(None, (prod_root(resolve(t, d)) for t in targets)), None)
        ask = ask or (root and f"Schreibzugriff in den Prod-Checkout {root}, den sonst nur der Deploy ändert.")
    if ask:
        decide("ask", ask)


def check_edit(path, cwd):
    p = resolve(path, cwd)
    root = prod_root(p)
    if root and os.path.basename(p) != ".env":
        decide("deny", f"{root} ist ein Prod-Checkout, den nur der Deploy aktualisiert (nur .env ist erlaubt).")


def main():
    try:  # UTF-8 unabhängig von der Standardkodierung
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
