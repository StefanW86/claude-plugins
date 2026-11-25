"""Gemeinsame Helfer der Hook-Tests."""
import json
import os
import shlex
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def run_script(path, stdin, env):
    if not isinstance(stdin, str):
        stdin = json.dumps(stdin)
    return subprocess.run([sys.executable, path], input=stdin, capture_output=True, encoding="utf-8", env=env,
                          timeout=10)  # Timeout wie in hooks.json


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


def make_repo(path, branch="main", commit=True):
    os.makedirs(path, exist_ok=True)
    git(path, "init", "-q", "-b", branch)
    if commit:
        git(path, "commit", "-q", "--allow-empty", "-m", "init")
    return path


def q(path):
    """Pfad für Befehle in Bash und PowerShell, auch unter Windows (dort sonst Backslash als Escape)."""
    return shlex.quote(path.replace("\\", "/"))
