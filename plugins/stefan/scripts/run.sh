#!/bin/sh
# Startet ein Hook-Skript mit Python 3: unter Linux python3, unter Windows (Git Bash) python bzw. py -3.
# Der Windows-Platzhalter python3.exe aus dem Store startet kein Python, darum dort erst prüfen.
script="$(dirname "$0")/$1"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) exec python3 "$script" ;;
esac
for py in python "py -3" python3; do
  if $py -c "import sys; sys.exit(sys.version_info[0] != 3)" >/dev/null 2>&1; then
    exec $py "$script"
  fi
done
echo "Hook $1: Python 3 fehlt. Installieren: winget install Python.Python.3.13" >&2
[ "$1" = guard.py ] && exit 2 || exit 1
