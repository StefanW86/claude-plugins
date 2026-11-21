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

## UI (bedienbar wie für einen Nutzer)
- Bedienelemente aus der UI-Bibliothek des Projekts (z. B. shadcn Date Picker statt `<input type="date">`), keine nativen Browser-Steuerelemente, außer die Spec verlangt es. Jeder Zustand passt zum Theme, auch geöffnete Menüs, Popover und Picker im Dunkelmodus.
- Was etwas öffnet (Karte, Zeile, Kachel), reagiert auf Klick bzw. Tap auf seiner ganzen Fläche, außer auf eigenen Bedienelementen darin; Hover und Zeiger zeigen das an.
- Drag & Drop: Das Ziel reagiert, sobald der Zeiger darüber ist (z. B. dnd-kit `pointerWithin`, Fallback `rectIntersection`), nicht erst bei großer Überlappung. Ein Klick ohne Bewegung bleibt ein Klick; auf Touch-Geräten wird per Halten gezogen.
- Mobile Zielplattformen: eigene Bedienung statt verkleinerter Desktop (Touch-Ziele ≥ 44 px, nichts nur per Hover, kein seitliches Scrollen der Seite).
- UI-Tests mit realistischen Gesten statt Idealfall: neben die Beschriftung klicken, beim Ziehen nur knapp (≈ ¼) ins Ziel, mobil per Tap im Geräteprofil. Ein UI-Test muss bei schlechter Bedienung rot werden.
