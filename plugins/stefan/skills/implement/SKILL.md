---
name: implement
description: Setzt per TDD um – eine Spec aus docs/specs/ Aufgabe für Aufgabe (allein oder als Orchestrator mit Subagenten) oder direkt ohne Spec einen Bugfix, eine kleine Änderung bzw. Befunde aus einem Bericht (UX-Review, Audit; Status wird im Bericht gepflegt) – und schließt immer mit Reviews ab (Security-Review und frischer Clone bei Bedarf). Verwenden, wenn die Programmierung einer Spec gestartet oder fortgesetzt, ein Bug behoben oder eine kleine Anpassung umgesetzt werden soll.
hooks:
  Stop:
    - hooks:
        - type: command
          command: sh "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh" open-tasks.py
---

# Spec umsetzen

## Start (auch zum Fortsetzen)
0. Lief in dieser Session schon andere Arbeit (z. B. Planung, Design) und hat der Nutzer nicht in `stefan:go` „hier weiter“ gewählt, empfehlen: `/clear`, dann erneut aufrufen; die Spec enthält alles. Der Nutzer entscheidet.
1. Projekt-`CLAUDE.md` beachten (Befehle, E2E-Weg, Nicht im Umfang, Integration). **Integration** = Zeile `Integration: <basis>, merge|mr`: Basis-Branch und Weg nach der Abnahme (`merge`: lokal mergen und pushen; `mr`: Branch pushen, Merge Request bzw. Pull Request anlegen, nicht selbst mergen). Fehlt sie, einmal per `AskUserQuestion` fragen (Empfehlung: Basis aus `origin/HEAD`, sonst `main`; Weg `merge`) und die Zeile in die Projekt-`CLAUDE.md` schreiben. `<basis>` steht unten für den Basis-Branch. Bugfix, kleine Änderung oder Bericht aus `docs/ux-review/` bzw. `docs/audit/` → Modus Direkt. Sonst angegebene Spec, sonst die neueste in `docs/specs/` mit offenen Aufgaben. Spec und `tasks.json` lesen. Im Modus groß die Aufgabendateien **nicht** selbst lesen.
2. Branch nach dem Schema aus `CLAUDE.md` (Projekt, `.claude/rules/`, global), sonst `feature/NNNN-<slug>`, von `<basis>` anlegen oder auschecken; der letzte Namensteil ist `NNNN-<slug>` oder `<slug>`, sonst greift der Stop-Hook nicht. `git status`, `git log --oneline -10`, Tests ausführen. Ist die Ausgangslage nicht grün, zuerst mit dem Nutzer klären.
3. **Vorab vom Nutzer** (Spec-Kopf) prüfen, soweit möglich (z. B. `gh secret list`); Fehlendes jetzt erfragen.
4. Spec-Status → `In Progress`. `blocked`-Aufgaben, deren Grund erledigt ist → `todo`. Weiter mit der ersten Aufgabe, die nicht `done` ist und deren Abhängigkeiten erledigt sind. Sind alle Aufgaben und `closing` `done`: nur die Abnahme einholen (Kurzbericht aus `closing.notes`).

## Rückfragen
Ist etwas unklar, per `AskUserQuestion` fragen (eine Entscheidung je Frage, Empfehlung zuerst), nicht raten. Ausnahme: Solange eine Spec `In Progress` ist, gilt der nächste Abschnitt.

## Ohne Rückfrage durcharbeiten
Solange die Spec `In Progress` ist, nicht fragen und nicht anhalten. Braucht etwas eine Entscheidung des Nutzers (z. B. ein Test scheint falsch, der Nutzer will pausieren) → betroffene bzw. nächste offene Aufgabe `blocked`, Grund in `notes`; weiter mit der nächsten Aufgabe, deren Abhängigkeiten nicht blockiert sind. Ein Stop-Hook schickt dich zurück, solange bearbeitbare Aufgaben oder der Abschluss offen sind.

## TDD (jede Aufgabe, jeder Fix)
Modus klein und Direkt: zu Beginn Skill `stefan:clean-code` laden (TDD, Tests, sparsam arbeiten), im selben Antwortblock wie die ersten Lese- und Statusbefehle, und danach arbeiten. Unerwarteter Fehler → Schritte 1–4 aus [references/bugfix.md](references/bugfix.md), kein Fix ohne belegte Ursache. Danach in `tasks.json` nur `status`, `commit`, `notes` der Aufgabe setzen.

## Modus klein
Diese Session arbeitet die Aufgaben nacheinander selbst ab.

## Modus groß
Diese Session orchestriert und schreibt keinen Produktivcode. Pro Aufgabe, streng nacheinander:
1. Subagent `stefan:task-implementer` im Vordergrund starten, mit `model` aus der Aufgabe in `tasks.json` (fehlt es: Standard des Agenten). Auftrag nur: Pfad der Aufgabendatei, Verzeichnis, Branch.
2. Bericht prüfen: Befehle mit Ausgabe vorhanden, rot → grün belegt? Hält er Test oder Aufgabe für falsch → `blocked`.
3. Frischen Subagent `stefan:task-reviewer` mit demselben `model` starten. Auftrag: Pfad der Aufgabendatei und Commit vor der Aufgabe.
4. Befunde am Code nachvollziehen; zutreffende von einem **frischen** `stefan:task-implementer` mit `model: sonnet` im Vordergrund beheben lassen (Auftrag: Befunde mit Datei:Zeile, Pfad der Aufgabendatei, Verzeichnis, Branch), nicht per SendMessage: der alte Kontext ist groß, und fortgesetzte Agenten laufen im Hintergrund. Fix prüfen: klein (nur Tests ergänzt oder ≤ ~20 Zeilen Produktivcode) → diese Session liest Diff und Testausgabe selbst; sonst frischer `stefan:task-reviewer` nur für den Fix (Auftrag: Befunde, Commit vor dem Fix). Scheitert die Aufgabe zweimal am Review: nächster Fix mit `model: opus`; scheitert auch er → `blocked`.
   Widersprechen sich Anforderungen bzw. Design (z. B. Touch-Ziel ≥ 44 px gegen dicht liegende Punkte), nicht per Fix entscheiden: `blocked`, im Abschluss den Nutzer fragen.
5. `tasks.json` aktualisieren.

## Modus Direkt (ohne Spec)
Aufruf mit Beschreibung oder Bericht statt Spec-Pfad. Diese Session arbeitet selbst, ohne Subagenten für die Umsetzung.
- **Branch** nach dem Schema aus `CLAUDE.md`, sonst `fix/<slug>` bzw. `feature/<slug>`, von `<basis>`.
- **Bugfix:** Vorgehen nach [references/bugfix.md](references/bugfix.md).
- **Befunde aus einem Bericht** (Aufruf `<bericht.md> [Nummern]`; UX-Review, Audit oder Bugfix-Liste aus `docs/ux-review/` bzw. `docs/audit/`): Ohne Nummern gelten alle Befunde mit Status `offen`. Ältere Berichte beim ersten Lauf ergänzen: Fehlt die Spalte „Status“, sie als letzte Spalte anfügen, überall `offen`; stehen die Befunde nur als Liste da, davor eine Tabelle `| # | Befund | Status |` setzen (fehlen Nummern: in Reihenfolge nummerieren). Nummern ändern sich nie. Jeder gewählte Befund ist ein Bugfix mit eigenem Test- und Fix-Commit; sein Fall ist die Feedback-Schleife. Unklar (Befund nicht nachvollziehbar, Vorschlag mehrdeutig oder gegen Design bzw. Spec, zu groß für den Modus Direkt) → per `AskUserQuestion` fragen: so umsetzen, offen lassen oder verwerfen. Den Stand schreibt Abschluss Schritt 6 in den Bericht.
- **Kleine Änderung** (ein Bereich, wenige Dateien): Unklares per `AskUserQuestion` in höchstens drei Fragen klären, Akzeptanzkriterien in 2–5 Zeilen nennen, ohne auf Bestätigung zu warten. Dann TDD: zuerst ein E2E- bzw. Akzeptanztest, der rot wird, danach Unit-Tests und Code. Design, Plattformen und Themes aus vorhandener Spec, Projekt-`CLAUDE.md` und Design-Canvas übernehmen.
- Wächst es darüber hinaus (neue Ansicht, Datenmodell, mehrere Bereiche) → anhalten und eine Spec über `stefan:plan-to-spec` vorschlagen.

## Abschluss (immer, in allen Modi)
Erst wenn keine Aufgabe mehr bearbeitbar ist. Sind Aufgaben `blocked`: nur Bericht mit den offenen Fragen, `closing` bleibt `todo`.
Schritte 0–6 in einem Zug: Ergebnisse von Review-Skills und Subagenten sind Zwischenstände, nie das Ende der Antwort; danach sofort mit dem nächsten Schritt weiter. Nur Schritt 6 berichtet an den Nutzer.
0. **Diät** (nur Modus groß und klein): Skill `simplify` mit Argument `<basis>...HEAD` (alles ist committet). Nur verhaltensgleiche Vereinfachungen übernehmen: Testfälle und Assertions bleiben, Performance-Vorschläge nur mit Messung. Was Verhalten ändert, kommt als Entscheidung in den Bericht. Betroffene Tests grün, Commit `refactor: …`. Im Modus groß übernimmt das ein frischer `stefan:task-implementer` mit `model: sonnet` im Vordergrund (Auftrag: „Diät“, dieser Schritt wörtlich, Verzeichnis, Branch); seinen Bericht wie in Modus groß Schritt 2 prüfen.
1. **Code-Review** des Branches gegen `<basis>`: Skill `code-review`, Stufe `medium` (im Modus groß sind die Aufgaben schon einzeln geprüft). Im Modus Direkt stattdessen ein frischer Subagent `stefan:task-reviewer` (Auftrag: Akzeptanzkriterien, Fehlerbeschreibung bzw. gewählte Befunde des Berichts, Commit vor der Änderung = `git merge-base <basis> HEAD`).
2. **Security-Review:** Skill `security-review`, nur wenn der Diff Eingaben von außen (Nutzer, API, Dateien, Netz) neu oder anders verarbeitet, Endpunkte, Auth bzw. Rechte, Secrets, Abhängigkeiten, Konfiguration oder CI ändert; reine Refactorings, feste Werte, Layout und Client-Darstellung nicht. Sonst im Bericht: „Security-Review entfällt: <Grund>“. Die in den Specs des Projekts bewusst akzeptierten Risiken (z. B. kein Login, nur LAN) sind keine Befunde.
3. **Bedienung wie ein Nutzer** (nur bei UI-Änderungen, deren Abläufe lokal mit Entwicklungs- bzw. Seed-Daten erreichbar sind; sonst im Bericht „ungeprüft: <Grund>“): Subagent `stefan:ui-walker`, in allen Modi (Screenshots belasten so nicht diese Session). Modus groß und klein: nach Schritt 0 im Hintergrund starten, 1 und 2 laufen parallel (beide ändern nichts). Modus Direkt: nach Schritt 1 im Vordergrund, weil der Reviewer Tests ausführt. Seinen Bericht vor Schritt 4 abwarten; ist sonst nichts zu tun, die Antwort mit einer Statuszeile beenden, seine Rückmeldung setzt fort. Auftrag: Verzeichnis, Branch, Spec-Pfad bzw. im Modus Direkt die Akzeptanzkriterien oder Bericht und gewählte Nummern, Test-Geräte und Themes, Umfang (Spec: jede User Story; Direkt: nur die betroffenen Abläufe).
4. **Befunde prüfen und einstufen:** Jeden Befund erst am Code nachvollziehen; unzutreffende begründet verwerfen und im Bericht nennen, nicht umsetzen. Critical (Sicherheitslücke, Datenverlust), High (Kernfunktion kaputt), Medium (Workaround nötig), Low (kosmetisch). Übernommenes Verhalten („wie bei X“, vorbestehend) wird nach seiner Auswirkung eingestuft, nicht niedriger. Critical, High und Medium beheben per TDD (erst ein Test, der die Lücke zeigt; im Modus groß per `stefan:task-implementer` mit `model: sonnet` und dem Befund statt Aufgabendatei). Fix prüfen wie in Modus groß Schritt 4, nicht das ganze Review erneut; bei Security-Befunden zusätzlich das Security-Review. Zielkonflikt (Modus groß Schritt 4) → vor dem Fix per `AskUserQuestion` fragen. Low als Entscheidungsliste in den Bericht (mit Bericht als Quelle zusätzlich als Folgepunkte, Schritt 6).
5. **Abschlussprüfungen:** ein frischer Subagent `stefan:closing-checker` im Vordergrund, in allen Modi (der Kontext dieser Session ist hier am größten). Auftrag: Verzeichnis, Branch, Test-Geräte der Spec und
   - gesamte Suite und E2E (mit UI auf allen Test-Geräten gegen einen Produktions-Build); lief beides in dieser Session nach der letzten Änderung am Produktivcode schon grün, nur die seither geänderten Tests,
   - frischer Clone (einziger im ganzen Ablauf) nur, wenn Build, Abhängigkeiten, Setup, Migrationen oder Konfiguration geändert wurden,
   - Vorschau bei UI-Änderungen.

   Fehlschläge wie Befunde in Schritt 4 beheben, dann nur das Fehlgeschlagene erneut prüfen lassen. Die Vorschau-URL erst nennen, wenn der Bericht sie über die LAN-Adresse als bedienbar meldet.
6. **Bericht an den Nutzer:** erledigte Aufgaben, Review-Ergebnisse, offene Befunde und Fragen, geprüfte Vorschau-URL. Am Ende „Geänderte Dateien“: Tabelle Datei | + | − aus `git diff --numstat <basis>...HEAD` mit Summenzeile (Lockfiles und Binärdateien als eine Zeile), darunter der Hinweis: Einzelheiten per `/diff` im Terminal bzw. Diff-Ansicht in Desktop und Web. Mit Spec: Kurzfassung in `closing.notes`, `closing.status` → `done`, committen. Mit Bericht als Quelle zuerst der Rückschrieb (unten). Erst nach Abnahme: ggf. Spec-Status → `Done` committen, Vorschau beenden, dann integrieren. Weg `merge`: Merge nach `<basis>` und Push, danach den gemergten Branch ohne Rückfrage löschen, als eigenen Befehl: lokal `git branch -d` (nur wenn git ihn als gemergt akzeptiert), auf `origin` `git push origin --delete`, falls er dort existiert; ebenso einen Worktree des Branches entfernen. Weg `mr`: Branch pushen, Merge Request bzw. Pull Request gegen `<basis>` anlegen (`gh pr create`, `glab mr create` oder ein passender Skill), Link nennen; der Branch bleibt bis zum Merge.

   **Rückschrieb in den Bericht** (Modus Direkt mit Bericht als Quelle, vor der Abnahme):
   - **Status** jedes gewählten Befunds: umgesetzt → `erledigt (<Hashes der fix-Commits>)`, verworfen → `verworfen: <Grund>`; offen gelassene bleiben `offen`.
   - **Folgepunkte:** was beim Umsetzen offen bleibt (Low-Befunde aus Code-Review, UI-Walk und Abschlussprüfung, „ungeprüft“, gleiche Fehlerursache an weiteren Stellen) als Abschnitt `## Folgepunkte aus der Umsetzung (<YYYY-MM-DD>)` anhängen: Tabelle `| # | Quelle | Befund | Vorschlag | Status |`, Nummern ab der höchsten im Bericht weiter, Status `offen`, nichts doppelt. Sie stehen zusätzlich im Chat-Bericht.
   - **Nächster Schritt** (Abschnitt bzw. Zeile, fehlt er: anhängen): `/stefan:implement <bericht> <noch offene Nummern>`, ist nichts mehr offen: „alles erledigt“.

   Dann nur den Bericht committen: `docs: <bericht> – Status`; so wird der Stand mit dem Branch integriert.

**Änderungswünsche statt Abnahme** (auch Low-Befunde): Mit Spec als neue Aufgaben ans Ende der Spec nach `stefan:plan-to-spec` Schritte 3, 4, 6 und 7, ohne Größenbewertung und ohne die Regeln für T01 und die letzte Aufgabe; der Modus bleibt, `closing.status` → `todo`; danach weiter mit Start Schritt 4. Im Modus Direkt: als weitere kleine Änderung bzw. weiteren Bugfix auf demselben Branch umsetzen, danach den Abschluss erneut; Folgepunkte per Nummer, ihr Status kommt mit dem erneuten Rückschrieb.
