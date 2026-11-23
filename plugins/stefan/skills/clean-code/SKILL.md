---
name: clean-code
description: Regeln für Code und Tests – TDD-Zyklus für Spec-Aufgaben und Bugfixes, Testqualität, Einfachheit, sparsames Arbeiten, dazu Terraform und PowerShell (Skripte, Module, Runbooks). Verwenden beim Schreiben, Refaktorieren oder Reviewen von Code oder Tests.
---

# Code und Tests

## TDD (Spec-Aufgaben und Bugfixes)
1. **Red:** Tests aus den Testfällen schreiben (bei Befund oder Bug: ein Test, der ihn zeigt), ausführen, Fehlschlag aus dem richtigen Grund bestätigen. Commit `test(Txx): …` bzw. `test(fix): …`.
2. **Green:** minimal implementieren bis grün. Tests dabei nicht ändern.
3. **Refactor:** aufräumen; gesamte Suite, Lint, Typecheck grün. Commit `feat(Txx): …` bzw. `fix: …`.

Commit-Messages ohne Co-Authored-By-Zeile (der Schutz-Hook lehnt sie ab).

## Sparsam arbeiten (jede Runde liest den ganzen Kontext neu)
- Mehrere Lese- bzw. Edit-Schritte und die anschließende Prüfung in einem Shell-Aufruf bündeln; unabhängige Aufrufe (Skill laden, Dateien lesen, Status prüfen) in einer Antwort parallel stellen.
- Gezielt lesen (`grep -n`, `sed -n a,bp` bzw. `Select-String`, Read mit offset/limit) statt ganzer Dateien; Gelesenes und Screenshots nicht erneut lesen.
- Ausgaben kürzen, Fehlermeldungen aber vollständig behalten, damit kein zweiter Lauf nur zum Lesen nötig ist: z. B. `--reporter=line 2>&1 | tail -40` statt `tail -3` (PowerShell: `Select-Object -Last 40`).
- Prüfstufen: während der Arbeit nur betroffene Tests; gesamte Suite, Lint, Typecheck und E2E einmal am Ende. Schlägt etwas fehl: nur die fehlgeschlagenen Tests bis grün, dann die Suite ein letztes Mal. `--repeat-each` nur bei konkretem Verdacht auf instabile Tests. Frischer Clone nur im Abschluss.
- Keine Testläufe neben einer noch laufenden Suite: die Last verfälscht Laufzeiten und Timeouts. Hintergrundläufe erst abwarten.

## Tests
- Verhalten an öffentlichen Schnittstellen (Seams) prüfen, nicht Interna.
- Erwartete Werte aus unabhängiger Quelle (Testfall, festes Beispiel), nie so berechnet wie im Code.
- Mocks nur an Systemgrenzen (externe APIs, Zeit, Zufall).

## Code
- Allgemeingültig lösen, keine Sonderfälle nur für Testdaten.
- Nur das Verlangte: keine „für später“-Parameter, Flags, Abstraktionen oder Konfigurierbarkeit.
- Vor dem Neubauen vorhandene Komponenten und Hilfsfunktionen suchen und wiederverwenden.
- Dieselbe Fachregel (Bedeutung einer Einstellung, Auswahl betroffener Datensätze, Validierung) steht nur an einer Stelle, schon ab dem zweiten Vorkommen. Bloß ähnliche Struktur erst ab drei Vorkommen extrahieren; nur zufällig Gleiches nicht zusammenlegen.
- Ein bestehendes Muster übernehmen heißt, es wie neuen Code zu prüfen: Mängel darin mit beheben oder melden, nicht mitkopieren.
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
