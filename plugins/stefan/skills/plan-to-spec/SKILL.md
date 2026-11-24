---
name: plan-to-spec
description: Erstellt eine umsetzungsfertige Spec mit Größenbewertung, TDD und sequenziellen Aufgaben – aus einem Plan in docs/plans/ oder, ohne Plan, aus einem vorherigen Interview. Verwenden, wenn eine Spec, spec.md oder Aufgabenliste für die Umsetzung entstehen soll.
---

# Plan → Spec

Die Spec sagt *wie, in welcher Reihenfolge und woran „fertig“ erkennbar ist*, so vollständig, dass eine frische Session ohne Rückfrage mit T01 beginnen kann. Nicht implementieren.

## Ablauf
1. **Eingabe klären:**
   - **Plan übergeben:** lesen. Nicht `Accepted` oder lückenhaft (auch fehlende Pflichtthemen aus `stefan:grill-with-docs`) → nur die Lücken per Interview (wie unten) klären.
   - **Kein Plan übergeben:** Liegt in `docs/plans/` ein passender Plan, kurz fragen, ob er gemeint ist. Sonst **Interview** nach Skill `stefan:grill-with-docs`, aber statt den Plan zu schreiben nach der Bestätigung direkt weiter mit Schritt 2.
   - **Design:** Ist laut `stefan:ui-design` ein Design nötig und gibt es für diesen Plan keine freigegebene Seite im Design-Canvas des Projekts → fragen, ob zuerst dieser Skill laufen soll. Das Design einmal im aktuellen Stand per Artifact-Tool lesen (`project/canvas.json`, dann nur die Artboards dieses Plans; der Nutzer kann von Hand geändert haben). Daraus Farben, Schriften, Komponenten, Ansichten und Zustände knapp in die Spec übernehmen und jeder Ansicht ihr Artboard zuordnen.
2. **Fakten selbst sammeln:** Andere Projekte des Nutzers nur für das, was der Plan ausdrücklich übernimmt (z. B. Deploy-Muster), per `Explore`-Subagent, nur Ergebnisliste zurück. Versionen: aktuelle stabile per Context7 bzw. Registry, nicht aus anderen Projekten kopieren. CLAUDE.md, Memory und passende Skills (z. B. `deploy-neue-app`) beachten.
3. **Lücken schließen:** Delegiertes („Left to the builder“) selbst entscheiden, mit Begründung. Bei Bibliotheken und Werkzeugen mindestens zwei aktuelle Optionen vergleichen, davon eine neuere; „wie in Projekt X“ allein ist kein Grund. Fehlt Nicht-Delegiertes oder widerspricht sich etwas → Nutzer fragen, eine Frage pro `AskUserQuestion`. Nichts über Plan oder Interview hinaus bauen.
4. **Aufgaben schneiden:**
   - Vertikal: jede Aufgabe ist ein lauffähiges, testbares Inkrement. T01 = Fundament (Projektstruktur aus Abschnitt 2, Test-Runner inkl. E2E auf allen Test-Viewports, Lint, Smoke-Test, alle Befehle laufen). Letzte = Deploy/CI (den frischen Clone prüft der Abschluss von `implement`).
   - Jede passt in eine Session (Faustregel ≤ ~300 Zeilen Produktivcode).
   - Testfälle direkt als Akzeptanzkriterien; jede nutzersichtbare Aufgabe hat mindestens einen E2E-Testfall, erst dann gilt sie als fertig. UI-Testfälle nach Abschnitt „UI“ in `stefan:clean-code` (realistische Gesten, jede Zielplattform). Jede Anforderung `REQ-xx` gehört zu mindestens einer Aufgabe.
5. **Größe bewerten:** Treffer zählen: ≥ 5 Aufgaben · ≥ 3 Schichten (DB, Server, UI, Deploy) · neues Projekt · ≥ ~800 Zeilen Code · externe Integration (Deploy, API, Auth).
   - 0–1 → **klein:** eine Session, keine Subagenten. Aufgaben stehen in der Spec.
   - ≥ 2 → **groß:** Orchestrator, ein Subagent pro Aufgabe (nacheinander), je Aufgabe ein frischer Review-Subagent. Jede Aufgabe bekommt eine **eigenständige Aufgabendatei**, damit der Subagent nur sie lesen muss, und in `tasks.json` ein `model`: `opus` nur für Architektur (z. B. T01 eines neuen Projekts) oder heikle Logik (Nebenläufigkeit, Sicherheit, Algorithmen, Drag & Drop, Migration von Bestandsdaten), sonst `sonnet`, auch für Deploy/CI, CRUD und Ansichten.
6. **Schreiben** nach [references/spec-template.md](references/spec-template.md):
   - **Projekt-`CLAUDE.md`** anlegen bzw. ergänzen, höchstens ~15 Zeilen, damit jeder Subagent es ohne Spec weiß: Befehle (Tabelle aus Abschnitt 2), E2E-Weg auf diesem Host (z. B. Browser per Docker), Vorschau-Weg (Produktions-Build, Port, LAN-URL), Design-URL, Plattformen/Themes, „Nicht im Umfang“ und bewusst akzeptierte Risiken.
   - `docs/specs/NNNN-<slug>.md` und `NNNN-<slug>.tasks.json`; bei „groß“ zusätzlich `docs/specs/NNNN-<slug>/Txx.md`. NNNN und Slug wie der Plan; ohne Plan: höchste Nummer in `docs/plans/` und `docs/specs/` + 1. Existiert die Spec → aktualisieren, Änderungen nennen.
   - Sprache des Plans bzw. Interviews. **Knapp halten**, weil jede Umsetzungs-Session sie liest: keine Begründungen aus dem Plan kopieren, keine Allgemeinplätze. Nur Projektspezifisches; den allgemeinen Ablauf (TDD, Subagenten, Reviews, Abschluss) regelt `stefan:implement`.
7. **Selbstprüfung:**
   - [ ] Jede User Story, jedes Ziel und jede Entscheidung aus Plan oder Interview ist durch ein `REQ-xx` abgedeckt, jeder Nicht-Umfang steht unter „Nicht im Umfang“.
   - [ ] Jede Zielplattform hat ein Test-Gerät (mobil mit Touch und passender Engine) und Artboards. Legt der Stack eine UI-Bibliothek fest, ist jedes Bedienelement einer ihrer Komponenten zugeordnet.
   - [ ] Jede Aufgabe hat Testfälle, jede nutzersichtbare einen E2E-Testfall; alle Befehle sind konkret, kein „TBD“.
   - [ ] Was nur der Nutzer liefern kann (Secrets, Tokens, Zugänge), steht unter „Vorab vom Nutzer“.
   - [ ] Bestehendes Projekt: Jede neue bzw. geänderte Anforderung ist gegen die vorhandenen Tests und Plattformvorgaben geprüft (`grep` in den Tests nach betroffenen Abläufen, Maßen, Geräten). Was bestehende Tests brechen würde, ist mit dem Nutzer geklärt und steht als bewusste Änderung samt anzupassender Tests in der Aufgabe.
   - [ ] Aufgaben, die dieselbe Datei oder Schnittstelle berühren, passen zusammen (was die eine erzeugt, nutzt die andere so).
   - [ ] Anforderungen widersprechen sich nicht (z. B. Touch-Ziel ≥ 44 px gegen dicht liegende Punkte); Konflikte hat der Nutzer entschieden.
   - [ ] Das Prüfskript (Abschnitt 2) startet Browser und Server nur, wenn sie nicht laufen, und baut nur nach Änderungen am Produktivcode neu; fehlt das im bestehenden Projekt, legt es T01 an.
   - [ ] Jeder E2E-Testfall findet seine Ausgangsdaten vor (Seed, Test- bzw. Staging-DB); fehlende Daten legt eine Aufgabe an oder sie stehen unter „Vorab vom Nutzer“.
   - [ ] Bei „groß“: Jede Aufgabendatei ist ohne Spec lösbar.
8. **Abschluss:** Pfad, Größe/Modus, Anzahl Aufgaben, wichtigste Builder-Entscheidungen und „Vorab vom Nutzer“ nennen. Empfehlen: Spec reviewen, dann in einer neuen Session `/stefan:implement docs/specs/NNNN-<slug>.md`.
