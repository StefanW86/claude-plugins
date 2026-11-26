# Web und PWA

## Bedienen
- **Werkzeug:** das E2E-Werkzeug des Projekts, sonst Playwright (Node, bei .NET-Projekten auch .NET). Skripte liegen im Scratchpad bzw. Temp-Verzeichnis, nicht im Repo.
- **Geräte ohne Vorgabe:**
  - Smartphone 390×844
  - Desktop 1440×900
  - bei einer PWA zusätzlich iPad 1024×1366

  Geräteprofile mit `deviceScaleFactor: 1` überschreiben. Hell und Dunkel per `colorScheme`.
- **Screenshot und Struktur:** `page.screenshot()` ohne `fullPage`; die ganze Seite nur bei Befunden zur Seitenlänge. Struktur per `locator('body').ariaSnapshot()`.
- **Echte Bedienung:** `click()` ohne `force`, kein `mouse.click(x, y)`. Scheitert Playwrights Prüfung auf Klickbarkeit (verdeckt, außerhalb des Bildschirms), ist genau das der Befund.
- **Rückmeldung:** `[role=status]`, `[role=alert]` und `[aria-live]` direkt nach der Aktion auslesen.

## Prüfen
- **Netz:** langsames Netz per CDP (`Network.emulateNetworkConditions`), offline per `context.setOffline(true)`; offline ist bei einer PWA Pflicht.
- **WCAG messen:**
  - mit `@axe-core/playwright`, wenn das Projekt es hat
  - sonst Kontrast aus den berechneten Farben (`getComputedStyle`) und Zielgröße aus `boundingBox()`
  - Tastatur: den Hauptablauf einmal nur per Tab und Enter, Fokus sichtbar
- **Richtwerte:** Touch-Ziel mindestens 44×44 pt (Apple) bzw. 48×48 dp (Material); nichts nur per Hover; kein seitliches Scrollen der Seite.
