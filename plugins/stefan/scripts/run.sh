#!/bin/sh
# Startet ein Python-Hook-Skript. Linux: python3. Windows (Git Bash): den echten python.exe; sein Pfad wird einmal
# ermittelt und in CLAUDE_PLUGIN_DATA (Skill-Hooks: Temp-Ordner) gemerkt, weil die Aliasse aus WindowsApps und
# py -3 bei jedem Aufruf Zeit kosten. Nur Shell-Builtins: unter Windows kostet jeder Prozessstart.
# Fehlt Python, laufen die Tools ohne diese Prüfung weiter, mit Warnung bei jedem Aufruf.
case $0 in *[/\\]*) script="${0%[/\\]*}/$1" ;; *) script="./$1" ;; esac
if [ "$OS" != Windows_NT ]; then
  command -v python3 >/dev/null 2>&1 && exec python3 "$script"
else
  cache="${CLAUDE_PLUGIN_DATA:-${TEMP:-/tmp}}/python-path"
  py=
  [ -f "$cache" ] && read -r py < "$cache"
  [ -n "$py" ] && [ -f "$py" ] && exec "$py" "$script"
  for cand in python "py -3" python3; do
    # Der Platzhalter python3.exe aus dem Store startet kein Python und fällt hier durch.
    py=$($cand -c "import sys; sys.version_info[0] == 3 and sys.stdout.write(sys.executable)" 2>/dev/null) || continue
    [ -n "$py" ] && [ -f "$py" ] || continue
    printf '%s\n' "$py" > "$cache" 2>/dev/null
    exec "$py" "$script"
  done
fi
printf '{"systemMessage": "Hook %s (Plugin stefan): Python 3 fehlt, die Pr\\u00fcfung ist aus. Installieren: winget install Python.Python.3.13"}\n' "$1"
exit 0
