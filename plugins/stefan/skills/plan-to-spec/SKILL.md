---
name: plan-to-spec
description: Erstellt eine umsetzungsfertige Spec mit Größenbewertung, TDD und sequenziellen Aufgaben – aus einem Plan in docs/plans/ oder, ohne Plan, aus einem vorherigen Interview. Verwenden, wenn eine Spec, spec.md oder Aufgabenliste für die Umsetzung entstehen soll.
---

# Plan → Spec

Die Spec sagt *wie, in welcher Reihenfolge und woran „fertig“ erkennbar ist*, so vollständig, dass eine frische Session ohne Rückfrage mit T01 beginnen kann. Nicht implementieren.

## Ablauf
1. **Eingabe klären:**
   - **Plan übergeben:** lesen. Nicht `Accepted` oder lückenhaft (auch fehlende Pflichtthemen aus `stefan:grill-with-docs`) → nur die Lücken per Interview (wie unten) klären.
   - **Kein Plan übergeben:** Liegt in `docs/plans/` ein passender Plan, kurz fragen, ob er gemeint ist. Sonst **Interview:** Skill `stefan:grill-with-docs` laden und dessen Pflichtthemen und Regeln zum Fragen, zu den Techniken und zum Abschluss befolgen. Abweichend davon keinen Plan schreiben, sondern nach der Bestätigung direkt mit Schritt 2 weitermachen. Der Nutzer entscheidet Ziel, Umfang, Nicht-Umfang, fachliches Verhalten und Constraints. Technische Details, die er nicht selbst festlegen will, werden Builder-Entscheidungen.
   - **Design:** Ist laut `stefan:ui-design` ein Design nötig und gibt es für diesen Plan keine freigegebene Seite im Design-Canvas des Projekts → fragen, ob zuerst dieser Skill laufen soll. Das Design einmal im aktuellen Stand per Artifact-Tool lesen (`project/canvas.json`, dann nur die Artboards dieses Plans; der Nutzer kann von Hand geändert haben). Daraus Farben, Schriften, Komponenten, Ansichten und Zustände knapp in die Spec übernehmen und jeder Ansicht ihr Artboard zuordnen.
2. **Fakten selbst sammeln:** Referenzprojekte aus den Constraints per `Explore`-Subagent (Stack, Versionen, Struktur, Test-Setup, Lint, Docker, CI, Deploy; nur Ergebnisliste zurück). Library-Versionen per Context7. CLAUDE.md, Memory und passende Skills (z. B. `deploy-neue-app`) beachten.
3. **Lücken schließen:** Delegiertes („Left to the builder“) selbst entscheiden, mit Begründung. Fehlt Nicht-Delegiertes oder widerspricht sich etwas → Nutzer fragen, eine Frage pro `AskUserQuestion`. Nichts über Plan oder Interview hinaus bauen.
4. **Aufgaben schneiden:**
   - Vertikal: jede Aufgabe ist ein lauffähiges, testbares Inkrement. T01 = Fundament (Projektstruktur aus Abschnitt 2, Test-Runner inkl. aller Test-Viewports, Lint, Smoke-Test, alle Befehle laufen). Letzte = Deploy/CI, E2E, Prüfung aus frischem Clone.
   - Jede passt in eine Session (Faustregel ≤ ~300 Zeilen Produktivcode).
   - Testfälle direkt als Akzeptanzkriterien. Jede Anforderung `R-xx` gehört zu mindestens einer Aufgabe.
5. **Größe bewerten:** Treffer zählen: ≥ 5 Aufgaben · ≥ 3 Schichten (DB, Server, UI, Deploy) · neues Projekt · ≥ ~800 Zeilen Code · externe Integration (Deploy, API, Auth).
   - 0–1 → **klein:** eine Session, keine Subagenten. Aufgaben stehen in der Spec.
   - ≥ 2 → **groß:** Orchestrator, ein Subagent pro Aufgabe (nacheinander), je Aufgabe ein frischer Review-Subagent. Jede Aufgabe bekommt eine **eigenständige Aufgabendatei**, damit der Subagent nur sie lesen muss, und in `tasks.json` ein `model`: `opus` für T01 und Aufgaben mit Architektur, breiter Integration oder heikler Logik (Nebenläufigkeit, Sicherheit, Algorithmen), sonst `sonnet`.
6. **Schreiben** nach [references/spec-template.md](references/spec-template.md):
   - `docs/specs/NNNN-<slug>.md` und `NNNN-<slug>.tasks.json`; bei „groß“ zusätzlich `docs/specs/NNNN-<slug>/Txx.md`. NNNN und Slug wie der Plan; ohne Plan: höchste Nummer in `docs/plans/` und `docs/specs/` + 1. Existiert die Spec → aktualisieren, Änderungen nennen.
   - Sprache des Plans bzw. Interviews. **Knapp halten**, weil jede Umsetzungs-Session sie liest: keine Begründungen aus dem Plan kopieren, keine Allgemeinplätze. Nur Projektspezifisches; den allgemeinen Ablauf (TDD, Subagenten, Reviews, Abschluss) regelt `stefan:implement-spec`.
7. **Selbstprüfung:**
   - [ ] Jede User Story, jedes Ziel und jede Entscheidung aus Plan oder Interview ist durch ein `R-xx` abgedeckt, jeder Nicht-Umfang steht unter „Nicht im Umfang“.
   - [ ] Jede Aufgabe hat Testfälle, alle Befehle sind konkret, kein „TBD“.
   - [ ] Aufgaben, die dieselbe Datei oder Schnittstelle berühren, passen zusammen (was die eine erzeugt, nutzt die andere so).
   - [ ] Bei „groß“: Jede Aufgabendatei ist ohne Spec lösbar.
8. **Abschluss:** Pfad, Größe/Modus, Anzahl Aufgaben und wichtigste Builder-Entscheidungen nennen. Empfehlen: Spec reviewen, dann in einer neuen Session `/stefan:implement-spec docs/specs/NNNN-<slug>.md`.
