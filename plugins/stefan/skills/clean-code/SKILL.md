---
name: clean-code
description: Regeln für Code und Tests – TDD-Zyklus für Spec-Aufgaben und Bugfixes, Testqualität, Einfachheit, sparsames Arbeiten, dazu Terraform und PowerShell (Skripte, Module, Runbooks). Verwenden beim Schreiben, Refaktorieren oder Reviewen von Code oder Tests.
---

# Code und Tests

Commit-Messages ohne Co-Authored-By-Zeile (der Schutz-Hook lehnt sie ab).

## TDD (Spec-Aufgaben und Bugfixes)
1. **Red:** Tests aus den Testfällen schreiben (bei Befund oder Bug: ein Test, der ihn zeigt), ausführen, Fehlschlag aus dem richtigen Grund bestätigen. Commit `test(Txx): …` bzw. `test(fix): …`.
2. **Green:** minimal implementieren bis grün. Tests dabei nicht ändern.
3. **Refactor:** aufräumen; gesamte Suite, Lint, Typecheck grün. Commit `feat(Txx): …` bzw. `fix: …`.

## Sparsam arbeiten (jede Runde liest den ganzen Kontext neu)
- Mehrere Lese- bzw. Edit-Schritte und die anschließende Prüfung in einem Shell-Aufruf bündeln; unabhängige Aufrufe (Skill laden, Dateien lesen, Status prüfen) in einer Antwort parallel stellen.
- Gezielt lesen (`grep -n`, `sed -n a,bp` bzw. `Select-String`, Read mit offset/limit) statt ganzer Dateien; Gelesenes und Screenshots nicht erneut lesen.
- Ausgaben kürzen, Fehlermeldungen aber vollständig behalten, damit kein zweiter Lauf nur zum Lesen nötig ist: z. B. `--reporter=line 2>&1 | tail -40` statt `tail -3` (PowerShell: `Select-Object -Last 40`).
- Keine Testläufe neben einer noch laufenden Suite: die Last verfälscht Laufzeiten und Timeouts. Hintergrundläufe erst abwarten.

## Prüfstufen
- Lint, Formatierung, statische und Security-Analyse ohne ausdrücklichen Wunsch nur für neue und geänderte Dateien (bzw. deren Module), nie fremde Altdateien; Tests und Typecheck laufen wie unten beschrieben.
- Während der Arbeit nur betroffene Tests, E2E dabei auf einem Test-Gerät (z. B. `--project`); gesamte Suite, Lint, Typecheck und E2E auf allen Geräten einmal am Ende, in einem Aufruf (Prüfskript des Projekts, sonst mit `&&` verkettet). Schlägt etwas fehl: nur die fehlgeschlagenen Tests bis grün (`--last-failed` bzw. Dateifilter), dann die Suite ein letztes Mal.
- E2E-Server (Weg aus Projekt-`CLAUDE.md`): neu bauen und neu starten nur, wenn sich Produktivcode seit dem letzten Build geändert hat, nicht nach reinen Teständerungen; mehrere Korrekturen sammeln, dann einmal bauen. Einen selbst gestarteten Server am Ende per PID beenden. `--repeat-each` nur bei konkretem Verdacht auf instabile Tests. Frischer Clone nur im Abschluss.

## Tests
- Verhalten an öffentlichen Schnittstellen (Seams) prüfen, nicht Interna.
- Erwartete Werte aus unabhängiger Quelle (Testfall, festes Beispiel), nie so berechnet wie im Code.
- Mocks nur an Systemgrenzen (externe APIs, Zeit, Zufall).
- Ohne UI ist E2E der Test auf oberster Ebene, z. B. `terraform test` oder Pester-Integrationstests (siehe Referenzen); Test-Geräte gibt es dann nicht.

## Code
- Allgemeingültig lösen, keine Sonderfälle nur für Testdaten.
- Einfachste Lösung, die das Verlangte erfüllt; mehr nur mit Beleg (Test, Messung). Keine „für später“-Parameter, Flags, Abstraktionen oder Konfigurierbarkeit.
- Keine Performance-Maßnahme (Memo, Deferred, Cache, Debounce) ohne Messung, die das Problem zeigt – auch nicht als Vorgabe in Spec oder Aufgabe. Fachlich begründetes Drosseln (z. B. API-Limit, Suche beim Tippen) zählt nicht als Performance-Maßnahme.
- Keinen Zustand anlegen (State, Ref, Puffer), der sich aus vorhandenem Zustand oder Eingaben ableiten lässt.
- Vor dem Neubauen vorhandene Komponenten und Hilfsfunktionen suchen und wiederverwenden.
- Dieselbe Fachregel (Bedeutung einer Einstellung, Auswahl betroffener Datensätze, Validierung) steht nur an einer Stelle, schon ab dem zweiten Vorkommen. Bloß ähnliche Struktur erst ab drei Vorkommen extrahieren; nur zufällig Gleiches nicht zusammenlegen. Identischen Code, auch Test-Helfer, importieren statt kopieren.
- Ein bestehendes Muster übernehmen heißt, es wie neuen Code zu prüfen: Mängel darin mit beheben oder melden, nicht mitkopieren.
- Braucht ein Fix einen Folgefix: zurückbauen und den einfacheren Weg suchen statt weiterflicken.
- Kommentare nur für das Warum, das der Code nicht zeigt; knapp, keine Spec-Wiederholung.
- Vor jedem Commit: Was kann weg, ohne dass sich Verhalten ändert (Code, Zustand, Kommentare, Kopien)?
- Je Modul bzw. Klasse eine eigene Datei.
- Bewusste Abweichung von einer Regel kurz begründen.
- Terraform (`*.tf` im Projekt oder in der Aufgabe): zusätzlich [references/terraform.md](references/terraform.md) lesen.
- PowerShell (`*.ps1`, `*.psm1`, `*.psd1` im Projekt oder in der Aufgabe): zusätzlich [references/powershell.md](references/powershell.md) lesen.

## UI (bedienbar wie für einen Nutzer)
- Legt der Tech-Stack eine UI-Komponentenbibliothek fest, kommt jedes Bedienelement aus ihr (z. B. deren Datumsauswahl statt eines nativen Datumsfelds); Eigenes nur für das, was sie nicht bietet. Jeder Zustand passt zum Theme, auch geöffnete Menüs, Popover und Auswahlfelder im Dunkelmodus.
- Was etwas öffnet (Karte, Zeile, Kachel), reagiert auf Klick bzw. Tap auf seiner ganzen Fläche, außer auf eigenen Bedienelementen darin; Hover und Zeiger zeigen das an.
- Drag & Drop: Das Ziel reagiert, sobald der Zeiger darüber ist (Erkennung nach Zeigerposition, nicht nach Flächenüberlappung). Ein Klick ohne Bewegung bleibt ein Klick; auf Touch-Geräten wird per Halten gezogen.
- Mobile Zielplattformen: eigene Bedienung statt verkleinerter Desktop (Touch-Ziele ≥ 44 px, nichts nur per Hover, kein seitliches Scrollen der Seite).
- UI-Tests mit realistischen Gesten statt Idealfall: neben die Beschriftung klicken, beim Ziehen nur knapp (≈ ¼) ins Ziel, mobil per Tap im Geräteprofil. Ein UI-Test muss bei schlechter Bedienung rot werden.
