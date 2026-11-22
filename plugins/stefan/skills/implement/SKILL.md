---
name: implement
description: Setzt per TDD um – eine Spec aus docs/specs/ Aufgabe für Aufgabe (allein oder als Orchestrator mit Subagenten) oder direkt ohne Spec einen Bugfix bzw. eine kleine Änderung – und schließt immer mit Code-Review, Security-Review und Prüfung aus frischem Clone ab. Verwenden, wenn die Programmierung einer Spec gestartet oder fortgesetzt, ein Bug behoben oder eine kleine Anpassung umgesetzt werden soll.
hooks:
  Stop:
    - hooks:
        - type: command
          command: sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" open-tasks.py
---

# Spec umsetzen

## Start (auch zum Fortsetzen)
0. Lief in dieser Session schon andere Arbeit (z. B. Planung, Design), empfehlen: `/clear`, dann erneut aufrufen; die Spec enthält alles. Der Nutzer entscheidet.
1. Projekt-`CLAUDE.md` beachten (Befehle, E2E-Weg, Nicht im Umfang). Bugfix oder kleine Änderung ohne Spec → Modus Direkt. Sonst angegebene Spec, sonst die neueste in `docs/specs/` mit offenen Aufgaben. Spec und `tasks.json` lesen. Im Modus groß die Aufgabendateien **nicht** selbst lesen.
2. Branch `feat/NNNN-<slug>` von `main` anlegen oder auschecken. `git status`, `git log --oneline -10`, Tests ausführen. Ist die Ausgangslage nicht grün, zuerst mit dem Nutzer klären.
3. **Vorab vom Nutzer** (Spec-Kopf) prüfen, soweit möglich (z. B. `gh secret list`); Fehlendes jetzt erfragen.
4. Spec-Status → `In Progress`. `blocked`-Aufgaben, deren Grund erledigt ist → `todo`. Weiter mit der ersten Aufgabe, die nicht `done` ist und deren Abhängigkeiten erledigt sind. Sind alle Aufgaben und `closing` `done`: nur die Abnahme einholen (Kurzbericht aus `closing.notes`).

## Ohne Rückfrage durcharbeiten
Solange die Spec `In Progress` ist, nicht fragen und nicht anhalten. Braucht etwas eine Entscheidung des Nutzers (z. B. ein Test scheint falsch, der Nutzer will pausieren) → betroffene bzw. nächste offene Aufgabe `blocked`, Grund in `notes`; weiter mit der nächsten Aufgabe, deren Abhängigkeiten nicht blockiert sind. Ein Stop-Hook schickt dich zurück, solange bearbeitbare Aufgaben oder der Abschluss offen sind.

## TDD (jede Aufgabe, jeder Fix)
Modus klein und Direkt: zu Beginn Skill `stefan:clean-code` laden (TDD, Tests, sparsam arbeiten) und danach arbeiten. Unerwarteter Fehler → Schritte 1–4 aus [references/bugfix.md](references/bugfix.md), kein Fix ohne belegte Ursache. Danach in `tasks.json` nur `status`, `commit`, `notes` der Aufgabe setzen.

## Modus klein
Diese Session arbeitet die Aufgaben nacheinander selbst ab.

## Modus groß
Diese Session orchestriert und schreibt keinen Produktivcode. Pro Aufgabe, streng nacheinander:
1. Subagent `stefan:task-implementer` im Vordergrund starten, mit `model` aus der Aufgabe in `tasks.json` (fehlt es: Standard des Agenten). Auftrag nur: Pfad der Aufgabendatei, Verzeichnis, Branch.
2. Bericht prüfen: Befehle mit Ausgabe vorhanden, rot → grün belegt? Hält er Test oder Aufgabe für falsch → `blocked`.
3. Frischen Subagent `stefan:task-reviewer` mit demselben `model` starten. Auftrag: Pfad der Aufgabendatei und Commit vor der Aufgabe.
4. Befunde am Code nachvollziehen; zutreffende von einem **frischen** `stefan:task-implementer` im Vordergrund beheben lassen (Auftrag: Befunde mit Datei:Zeile, Pfad der Aufgabendatei, Verzeichnis, Branch), nicht per SendMessage: der alte Kontext ist groß, und fortgesetzte Agenten laufen im Hintergrund. Danach frischer `stefan:task-reviewer` nur für den Fix (Auftrag: Befunde, Commit vor dem Fix). Scheitert die Aufgabe zweimal am Review → `blocked`.
5. `tasks.json` aktualisieren.

## Modus Direkt (ohne Spec)
Aufruf mit Beschreibung statt Spec-Pfad. Diese Session arbeitet selbst, ohne Subagenten für die Umsetzung.
- **Bugfix:** Branch `fix/<slug>` von `main`, Vorgehen nach [references/bugfix.md](references/bugfix.md).
- **Kleine Änderung** (ein Bereich, wenige Dateien): Branch `feat/<slug>` von `main`. Unklares in höchstens drei Fragen klären, Akzeptanzkriterien in 2–5 Zeilen nennen, ohne auf Bestätigung zu warten. Dann TDD: zuerst ein E2E- bzw. Akzeptanztest, der rot wird, danach Unit-Tests und Code. Design, Plattformen und Themes aus vorhandener Spec, Projekt-`CLAUDE.md` und Design-Canvas übernehmen.
- Wächst es darüber hinaus (neue Ansicht, Datenmodell, mehrere Bereiche) → anhalten und eine Spec über `stefan:plan-to-spec` vorschlagen.

## Abschluss (immer, in allen Modi)
Erst wenn keine Aufgabe mehr bearbeitbar ist. Sind Aufgaben `blocked`: nur Bericht mit den offenen Fragen, `closing` bleibt `todo`.
Schritte 1–8 in einem Zug: Ergebnisse von Review-Skills und Subagenten sind Zwischenstände, nie das Ende der Antwort; danach sofort mit dem nächsten Schritt weiter. Nur Schritt 8 berichtet an den Nutzer.
1. **Code-Review** des Branches gegen `main`: Skill `code-review`, Stufe `medium` (klein) bzw. `high` (groß). Im Modus Direkt stattdessen ein frischer Subagent `stefan:task-reviewer` (Auftrag: Akzeptanzkriterien bzw. Fehlerbeschreibung, Commit vor der Änderung = `git merge-base main HEAD`).
2. **Security-Review:** Skill `security-review`, nur wenn der Diff Server-Code (API, Server Actions, Datenbank), Auth, Abhängigkeiten, Konfiguration, CI oder Secrets berührt oder neu mit Nutzereingaben umgeht; reines Layout und Client-Darstellung nicht. Sonst im Bericht: „Security-Review entfällt: <Grund>“. Die in den Specs des Projekts bewusst akzeptierten Risiken (z. B. kein Login, nur LAN) sind keine Befunde.
3. **Bedienung wie ein Nutzer** (nur bei UI-Änderungen): Subagent `stefan:ui-walker` im Vordergrund, in allen Modi (Screenshots belasten so nicht diese Session). Auftrag: Verzeichnis, Branch, Spec-Pfad bzw. im Modus Direkt die Akzeptanzkriterien, Test-Geräte und Themes, Umfang (Spec: jede User Story; Direkt: nur die betroffenen Abläufe).
4. **Befunde prüfen und einstufen:** Jeden Befund erst am Code nachvollziehen; unzutreffende begründet verwerfen und im Bericht nennen, nicht umsetzen. Critical (Sicherheitslücke, Datenverlust), High (Kernfunktion kaputt), Medium (Workaround möglich), Low (kosmetisch). Critical, High und Medium beheben per TDD (erst ein Test, der die Lücke zeigt; im Modus groß per `stefan:task-implementer` mit dem Befund statt Aufgabendatei). Danach prüft ein frischer `stefan:task-reviewer` nur den Fix (Auftrag: Befunde, Commit vor dem Fix), nicht das ganze Review erneut; bei Security-Befunden zusätzlich das Security-Review. Low als Entscheidungsliste in den Bericht.
5. **Alle Zielplattformen:** gesamte Suite und E2E auf allen Test-Geräten der Spec, gegen eine lokale Instanz, nie gegen Prod. Lief beides in dieser Session nach der letzten Änderung am Produktivcode schon grün, genügen die seither geänderten Tests.
6. **Frischer Clone** (einziger im ganzen Ablauf) (im Modus Direkt nur, wenn Build, Abhängigkeiten oder Setup geändert): Branch in ein temporäres Verzeichnis klonen, install → build → test grün.
7. **Vorschau** (bei UI-Änderungen): so starten, wie Prod läuft (Produktions-Build bzw. Container, Weg aus Projekt-`CLAUDE.md`), auf eigenem Port mit Entwicklungsdaten, nie mit Prod-Daten. Die URL mit LAN-Adresse erst nennen, nachdem sie über genau diese Adresse bedienbar ist: mit dem E2E-Werkzeug öffnen und ein Bedienelement auslösen; HTTP 200 allein genügt nicht.
8. **Bericht an den Nutzer:** erledigte Aufgaben, Review-Ergebnisse, offene Befunde und Fragen, geprüfte Vorschau-URL. Mit Spec: Kurzfassung in `closing.notes`, `closing.status` → `done`, committen. Erst nach Abnahme: ggf. Spec-Status → `Done` committen, dann Merge nach `main` und Push, Vorschau beenden. Danach den gemergten Branch ohne Rückfrage löschen, als eigenen Befehl: lokal `git branch -d` (nur wenn git ihn als gemergt akzeptiert), auf `origin` `git push origin --delete`, falls er dort existiert; ebenso einen Worktree des Branches entfernen.
