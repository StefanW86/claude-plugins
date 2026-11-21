---
name: clean-code
description: Regeln für Code und Tests – TDD-Zyklus für Spec-Aufgaben und Bugfixes, Testqualität, Einfachheit. Verwenden beim Schreiben, Refaktorieren oder Reviewen von Code oder Tests.
---

# Code und Tests

## TDD (Spec-Aufgaben und Bugfixes)
1. **Red:** Tests aus den Testfällen schreiben (bei Befund oder Bug: ein Test, der ihn zeigt), ausführen, Fehlschlag aus dem richtigen Grund bestätigen. Commit `test(Txx): …` bzw. `test(fix): …`.
2. **Green:** minimal implementieren bis grün. Tests dabei nicht ändern.
3. **Refactor:** aufräumen; gesamte Suite, Lint, Typecheck grün. Commit `feat(Txx): …` bzw. `fix: …`.

## Tests
- Verhalten an öffentlichen Schnittstellen (Seams) prüfen, nicht Interna.
- Erwartete Werte aus unabhängiger Quelle (Testfall, festes Beispiel), nie so berechnet wie im Code.
- Mocks nur an Systemgrenzen (externe APIs, Zeit, Zufall).

## Code
- Allgemeingültig lösen, keine Sonderfälle nur für Testdaten.
- Nur das Verlangte: keine „für später“-Parameter, Flags, Abstraktionen oder Konfigurierbarkeit.
- Vor dem Neubauen vorhandene Komponenten und Hilfsfunktionen suchen und wiederverwenden.
- Gleiche Logik erst ab drei Vorkommen extrahieren; nur zufällig Gleiches nicht zusammenlegen.
- Je Modul bzw. Klasse eine eigene Datei.
- Bewusste Abweichung von einer Regel kurz begründen.
