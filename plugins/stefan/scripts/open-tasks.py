#!/usr/bin/env python3
"""Stop-Hook von implement: schickt Claude zurück an die Arbeit, solange auf dem Branch
feat/NNNN-… die Spec NNNN In Progress ist und bearbeitbare Aufgaben oder der Abschluss offen sind.
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


def find_repo(cwd):
    """Projektverzeichnis vor cwd, damit z. B. ein frischer Clone im Abschluss nicht zählt."""
    for d in (os.environ.get("CLAUDE_PROJECT_DIR"), cwd):
        m = re.match(r"feat/(\d{4})-", git(d, "branch", "--show-current")) if d else None
        if m:
            return git(d, "rev-parse", "--show-toplevel"), m.group(1)
    return None, None


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
        data = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    root, nnnn = find_repo(data.get("cwd") or os.getcwd())
    if not root:
        return 0
    for path in sorted(glob.glob(os.path.join(root, "docs", "specs", f"{nnnn}-*.tasks.json"))):
        msg = problem(root, path)
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": msg}}))
            return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
