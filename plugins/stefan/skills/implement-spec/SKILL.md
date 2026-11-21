---
name: implement-spec
description: Setzt eine Spec aus docs/specs/ Aufgabe für Aufgabe per TDD um – allein oder als Orchestrator mit Subagenten – und schließt immer mit Code-Review, Security-Review und Prüfung aus frischem Clone ab. Verwenden, wenn die Programmierung einer Spec gestartet oder fortgesetzt oder ein Bugfix ohne Spec umgesetzt werden soll.
---

# Spec umsetzen

## Start (auch zum Fortsetzen)
0. Lief in dieser Session schon andere Arbeit (z. B. Planung, Design), empfehlen: `/clear`, dann erneut aufrufen; die Spec enthält alles. Der Nutzer entscheidet.
1. Bugfix ohne Spec → Modus Bugfix. Sonst angegebene Spec, sonst die neueste in `docs/specs/` mit offenen Aufgaben. Spec und `tasks.json` lesen. Im Modus groß die Aufgabendateien **nicht** selbst lesen.
2. Branch `feat/NNNN-<slug>` von `main` anlegen oder auschecken. Spec-Status `Ready` → `In Progress`. `git status`, `git log --oneline -10`, Tests ausführen. Ist die Ausgangslage nicht grün, zuerst mit dem Nutzer klären.
3. Weiter mit der ersten Aufgabe, die nicht `done` ist und deren Abhängigkeiten erledigt sind.

## TDD (jede Aufgabe, jeder Fix)
1. **Red:** Tests aus den Testfällen schreiben, ausführen, Fehlschlag aus dem richtigen Grund bestätigen. Commit `test(Txx): …`.
2. **Green:** minimal implementieren bis grün. Tests nicht ändern; ist einer falsch → anhalten, begründen, der Nutzer entscheidet.
3. **Refactor:** aufräumen; gesamte Suite, Lint, Typecheck grün. Commit `feat(Txx): …`.

Gute Tests prüfen Verhalten an den Seams der Spec, nicht Interna. Erwartete Werte stammen aus einer unabhängigen Quelle (Testfall, festes Beispiel), nie so berechnet wie im Code. Mocks nur an Systemgrenzen (externe APIs, Zeit, Zufall). Vor dem Neubauen vorhandene Komponenten und Hilfsfunktionen suchen und wiederverwenden.

Unerwarteter Fehler → Schritte 1–4 aus [references/bugfix.md](references/bugfix.md), kein Fix ohne belegte Ursache.

Danach in `tasks.json` nur `status`, `commit`, `notes` der Aufgabe setzen.

## Modus klein
Diese Session arbeitet die Aufgaben nacheinander selbst ab.

## Modus groß
Diese Session orchestriert und schreibt keinen Produktivcode. Pro Aufgabe, streng nacheinander:
1. Subagent `stefan:task-implementer` im Vordergrund starten, mit `model` aus der Aufgabe in `tasks.json` (fehlt es: Standard des Agenten). Auftrag nur: Pfad der Aufgabendatei, Verzeichnis, Branch.
2. Bericht prüfen: Befehle mit Ausgabe vorhanden, rot → grün belegt?
3. Frischen Subagent `stefan:task-reviewer` mit demselben `model` starten. Auftrag: Pfad der Aufgabendatei und Commit vor der Aufgabe.
4. Befunde am Code nachvollziehen; zutreffende vom selben Implementierer beheben lassen (SendMessage), dann erneut prüfen.
5. `tasks.json` aktualisieren.

Anhalten und den Nutzer fragen, wenn eine Aufgabe zweimal am Review scheitert oder ein Test geändert werden müsste.

## Modus Bugfix (ohne Spec)
Branch `fix/<slug>` von `main`, Vorgehen nach [references/bugfix.md](references/bugfix.md). Wächst es über einen kleinen Fix hinaus (neues Verhalten, mehrere Bereiche) → anhalten und eine Spec über `stefan:plan-to-spec` vorschlagen.

## Abschluss (immer, in allen Modi)
1. **Code-Review** des Branches gegen `main`: Skill `code-review`, Stufe `medium` (klein, Bugfix) bzw. `high` (groß).
2. **Security-Review:** Skill `security-review`. Die in den Specs des Projekts bewusst akzeptierten Risiken (z. B. kein Login, nur LAN) sind keine Befunde.
3. **Befunde prüfen und einstufen:** Jeden Befund erst am Code nachvollziehen; unzutreffende begründet verwerfen und im Bericht nennen, nicht umsetzen. Critical (Sicherheitslücke, Datenverlust), High (Kernfunktion kaputt), Medium (Workaround möglich), Low (kosmetisch). Critical und High beheben per TDD (erst ein Test, der die Lücke zeigt; im Modus groß per `stefan:task-implementer` mit dem Befund statt Aufgabendatei), danach das betroffene Review erneut. Medium und Low dem Nutzer vorlegen, er entscheidet.
4. **Alle Zielplattformen:** gesamte Suite und E2E auf allen Test-Viewports bzw. Geräten der Spec, gegen eine lokale Instanz, nie gegen Prod.
5. **Frischer Clone** (bei Bugfix nur, wenn Build, Abhängigkeiten oder Setup geändert): Branch in ein temporäres Verzeichnis klonen, install → build → test grün.
6. **Bericht an den Nutzer:** erledigte Aufgaben, Review-Ergebnisse, offene Befunde. Erst nach seiner Abnahme: ggf. Spec-Status → `Done` committen, dann Merge nach `main` und Push.
