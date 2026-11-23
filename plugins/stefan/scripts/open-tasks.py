#!/usr/bin/env python3
"""Stop-Hook von implement: schickt Claude zurück an die Arbeit, solange auf dem Branch einer Spec
diese In Progress ist und bearbeitbare Aufgaben oder der Abschluss offen sind. Branch einer Spec
NNNN-<slug>: letzter Pfadteil ist <slug> oder beginnt mit NNNN- (feat/0003-x, feature/x, bug/0003-y).
blocked heißt: wartet auf den Nutzer, ebenso alles, was davon abhängt. Der Hinweis kommt als
additionalContext: Claude arbeitet weiter, ohne dass die Oberfläche einen Hook-Fehler meldet.
"""
import glob
import json
import os
import re
import subprocess
import sys


def git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def specs_on_branch(cwd):
    """tasks.json-Dateien der Specs, zu denen der Branch gehört. Projektverzeichnis vor cwd,
    damit z. B. ein frischer Clone im Abschluss nicht zählt."""
    for d in filter(None, (os.environ.get("CLAUDE_PROJECT_DIR"), cwd)):
        tail = git(d, "branch", "--show-current").rsplit("/", 1)[-1]
        root = git(d, "rev-parse", "--show-toplevel")
        if not tail or not root:
            continue
        paths = []
        for path in sorted(glob.glob(os.path.join(root, "docs", "specs", "*.tasks.json"))):
            m = re.match(r"(\d{4})-(.+)\.tasks\.json$", os.path.basename(path))
            if m and (tail == m.group(2) or tail.startswith(m.group(1) + "-")):
                paths.append(path)
        if paths:
            return root, paths
    return None, []


def problem(root, path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        with open(os.path.join(root, data["spec"]), encoding="utf-8") as f:
            spec = f.read()
        tasks = {t["id"]: t for t in data["tasks"]}
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not re.search(r"\*\*Status:\*\*\s*In Progress", spec):
        return None

    def waits(tid, seen=()):
        t = tasks.get(tid)
        if t is None or tid in seen:
            return False
        return t.get("status") == "blocked" or any(waits(d, seen + (tid,)) for d in t.get("dependsOn", []))

    todo = [tid for tid, t in tasks.items() if t.get("status") in ("todo", "in_progress") and not waits(tid)]
    if todo:
        return (f"{data['spec']}: offene Aufgaben {', '.join(todo)}. Weiterarbeiten. Nur wenn eine Entscheidung "
                "des Nutzers nötig ist (auch Pause): Aufgabe auf blocked setzen, Grund in notes.")
    closing = data.get("closing")
    blocked = any(t.get("status") == "blocked" for t in tasks.values())
    if isinstance(closing, dict) and closing.get("status") != "done" and not blocked:
        return (f"{data['spec']}: Aufgaben erledigt, Abschluss offen (Reviews, frischer Clone, Bericht; "
                "danach closing.status auf done).")
    return None


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    root, paths = specs_on_branch(data.get("cwd") or os.getcwd())
    for path in paths:
        msg = problem(root, path)
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": msg}}))
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
