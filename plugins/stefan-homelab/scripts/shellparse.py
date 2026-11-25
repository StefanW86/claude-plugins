"""Zerlegt Shell-Befehle (Bash, PowerShell) für die Schutz-Hooks.

Identische Kopie in den Plugins stefan und stefan-homelab, weil jedes Plugin für sich installiert wird;
tests/test_homelab.py prüft, dass beide gleich sind. Textabgleich ist ein Sicherheitsnetz, keine Sicherheitsgrenze.
"""
import os
import re
import shlex

CD_CMDS = {"cd", "pushd", "set-location", "sl", "chdir", "push-location"}
PREFIXES = {"sudo", "nohup", "time", "command", "exec", "env"}
SEPARATORS = {";", "&&", "||", "|", "&", "|&", ";;", "(", ")"}
HEREDOC = re.compile(r"(<<-?\s*(['\"]?)(\w+)\2)([^\n]*)\n.*?^[ \t]*\3[ \t]*$", re.S | re.M)


def resolve(path, base):
    m = re.match(r"^/([a-zA-Z])(/|$)", path) if os.name == "nt" else None
    if m:  # Git-Bash-Pfad /c/... → C:/...
        path = f"{m.group(1)}:/{path[3:]}"
    return os.path.realpath(os.path.join(base, os.path.expanduser(path)))


def segments(command):
    """Einfache Befehle als (Trenner davor, Tokens); Heredoc-Inhalte zählen nicht als Befehle."""
    command = HEREDOC.sub(r"\1\4", command.replace("\\\n", " "))
    try:
        lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:  # unvollständige Quotes: grob zerlegen
        return [("", s.split()) for s in re.split(r"&&|\|\||[;|&()\n]", command)]
    result, sep, seg = [], "", []
    for tok in tokens:
        if tok in SEPARATORS:
            result.append((sep, seg))
            sep, seg = tok, []
        else:
            seg.append(tok)
    return result + [(sep, seg)]


def command_name(word):
    name = os.path.basename(word.replace("\\", "/")).lower()
    return name[:-4] if name.endswith(".exe") else name


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


def commands(command, cwd, powershell=False):
    """(Name, Tokens, Trenner davor, Verzeichnis) je einfachem Befehl. cd bzw. Set-Location gilt für die
    folgenden Befehle und wird selbst nicht geliefert."""
    if powershell:  # Backslash ist dort Pfadtrenner, kein Escape
        command = command.replace("\\", "/")
    d = cwd
    for sep, seg in segments(command):
        seg = strip_prefixes(seg)
        if not seg:
            continue
        name = command_name(seg[0])
        if name in CD_CMDS and len(seg) > 1:
            d = resolve(next((a for a in seg[1:] if not a.startswith("-")), "."), d)
            continue
        yield name, seg, sep, d
