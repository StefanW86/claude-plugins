---
name: implement-spec
description: Setzt eine Spec aus docs/specs/ Aufgabe für Aufgabe per TDD um – allein oder als Orchestrator mit Subagenten – und schließt immer mit Code-Review, Security-Review und Prüfung aus frischem Clone ab. Verwenden, wenn die Programmierung einer Spec gestartet oder fortgesetzt oder ein Bugfix ohne Spec umgesetzt werden soll.
hooks:
  Stop:
    - hooks:
        - type: command
          command: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/open-tasks.py"
---

# Spec umsetzen

## Start (auch zum Fortsetzen)
0. Lief in dieser Session schon andere Arbeit (z. B. Planung, Design), empfehlen: `/clear`, dann erneut aufrufen; die Spec enthält alles. Der Nutzer entscheidet.
1. Projekt-`CLAUDE.md` beachten (Befehle, E2E-Weg, Nicht im Umfang). Bugfix ohne Spec → Modus Bugfix. Sonst angegebene Spec, sonst die neueste in `docs/specs/` mit offenen Aufgaben. Spec und `tasks.json` lesen. Im Modus groß die Aufgabendateien **nicht** selbst lesen.
2. Branch `feat/NNNN-<slug>` von `main` anlegen oder auschecken. `git status`, `git log --oneline -10`, Tests ausführen. Ist die Ausgangslage nicht grün, zuerst mit dem Nutzer klären.
3. **Vorab vom Nutzer** (Spec-Kopf) prüfen, soweit möglich (z. B. `gh secret list`); Fehlendes jetzt erfragen.
4. Spec-Status → `In Progress`. `blocked`-Aufgaben, deren Grund erledigt ist → `todo`. Weiter mit der ersten Aufgabe, die nicht `done` ist und deren Abhängigkeiten erledigt sind. Sind alle Aufgaben und `closing` `done`: nur die Abnahme einholen (Kurzbericht aus `closing.notes`).

## Ohne Rückfrage durcharbeiten
Solange die Spec `In Progress` ist, nicht fragen und nicht anhalten. Braucht etwas eine Entscheidung des Nutzers (z. B. ein Test scheint falsch, der Nutzer will pausieren) → betroffene bzw. nächste offene Aufgabe `blocked`, Grund in `notes`; weiter mit der nächsten Aufgabe, deren Abhängigkeiten nicht blockiert sind. Ein Stop-Hook schickt dich zurück, solange bearbeitbare Aufgaben oder der Abschluss offen sind.

## TDD (jede Aufgabe, jeder Fix)
Nach Skill `stefan:clean-code`. Unerwarteter Fehler → Schritte 1–4 aus [references/bugfix.md](references/bugfix.md), kein Fix ohne belegte Ursache. Danach in `tasks.json` nur `status`, `commit`, `notes` der Aufgabe setzen.

## Modus klein
Diese Session arbeitet die Aufgaben nacheinander selbst ab.

## Modus groß
Diese Session orchestriert und schreibt keinen Produktivcode. Pro Aufgabe, streng nacheinander:
1. Subagent `stefan:task-implementer` im Vordergrund starten, mit `model` aus der Aufgabe in `tasks.json` (fehlt es: Standard des Agenten). Auftrag nur: Pfad der Aufgabendatei, Verzeichnis, Branch.
2. Bericht prüfen: Befehle mit Ausgabe vorhanden, rot → grün belegt? Hält er Test oder Aufgabe für falsch → `blocked`.
3. Frischen Subagent `stefan:task-reviewer` mit demselben `model` starten. Auftrag: Pfad der Aufgabendatei und Commit vor der Aufgabe.
4. Befunde am Code nachvollziehen; zutreffende von einem **frischen** `stefan:task-implementer` im Vordergrund beheben lassen (Auftrag: Befunde mit Datei:Zeile, Pfad der Aufgabendatei, Verzeichnis, Branch), nicht per SendMessage: der alte Kontext ist groß, und fortgesetzte Agenten laufen im Hintergrund. Danach frischer `stefan:task-reviewer` nur für den Fix (Auftrag: Befunde, Commit vor dem Fix). Scheitert die Aufgabe zweimal am Review → `blocked`.
5. `tasks.json` aktualisieren.

## Modus Bugfix (ohne Spec)
Branch `fix/<slug>` von `main`, Vorgehen nach [references/bugfix.md](references/bugfix.md). Wächst es über einen kleinen Fix hinaus (neues Verhalten, mehrere Bereiche) → anhalten und eine Spec über `stefan:plan-to-spec` vorschlagen.

## Abschluss (immer, in allen Modi)
Erst wenn keine Aufgabe mehr bearbeitbar ist. Sind Aufgaben `blocked`: nur Bericht mit den offenen Fragen, `closing` bleibt `todo`.
1. **Code-Review** des Branches gegen `main`: Skill `code-review`, Stufe `medium` (klein, Bugfix) bzw. `high` (groß).
2. **Security-Review:** Skill `security-review`. Die in den Specs des Projekts bewusst akzeptierten Risiken (z. B. kein Login, nur LAN) sind keine Befunde.
3. **Bedienung wie ein Nutzer** (nur bei UI-Änderungen): Auf jedem Test-Gerät und in jedem Theme der Spec jede User Story einmal mit dem E2E-Werkzeug gegen eine lokale Instanz durchspielen, mit realistischen Gesten nach Abschnitt „UI“ in `stefan:clean-code`. Screenshots inkl. geöffneter Elemente ansehen und mit dem Design vergleichen. Jede Abweichung ist ein Befund; ist eine Funktion auf einer Zielplattform unbrauchbar, ist das High.
4. **Befunde prüfen und einstufen:** Jeden Befund erst am Code nachvollziehen; unzutreffende begründet verwerfen und im Bericht nennen, nicht umsetzen. Critical (Sicherheitslücke, Datenverlust), High (Kernfunktion kaputt), Medium (Workaround möglich), Low (kosmetisch). Critical, High und Medium beheben per TDD (erst ein Test, der die Lücke zeigt; im Modus groß per `stefan:task-implementer` mit dem Befund statt Aufgabendatei), danach das betroffene Review erneut. Low als Entscheidungsliste in den Bericht.
5. **Alle Zielplattformen:** gesamte Suite und E2E auf allen Test-Geräten der Spec, gegen eine lokale Instanz, nie gegen Prod.
6. **Frischer Clone** (einziger im ganzen Ablauf) (bei Bugfix nur, wenn Build, Abhängigkeiten oder Setup geändert): Branch in ein temporäres Verzeichnis klonen, install → build → test grün.
7. **Bericht an den Nutzer:** erledigte Aufgaben, Review-Ergebnisse, offene Befunde und Fragen. Mit Spec: Kurzfassung in `closing.notes`, `closing.status` → `done`, committen. Erst nach Abnahme: ggf. Spec-Status → `Done` committen, dann Merge nach `main` und Push.
