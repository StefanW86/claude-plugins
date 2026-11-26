# Windows-Desktop (WPF, WinUI 3, WinForms, Win32, UWP, Avalonia)

## Bedienen
Nur auf einem Windows-Host prüfbar. Auf einem anderen Host: als „nicht prüfbar“ melden und dazusagen, dass die Session auf dem Windows-Rechner gestartet werden muss.

- **Werkzeug:** das E2E-Werkzeug des Projekts, sonst FlaUI (UIA3) in einem Konsolenprojekt im Scratchpad bzw. Temp-Verzeichnis (`dotnet new console`, Paket `FlaUI.UIA3`). Shell ist PowerShell.
  - Web-Inhalte in der App (WebView2, Blazor Hybrid): mit Playwright per `connectOverCDP` prüfen, nach [web.md](web.md). WebView2 startest du dafür mit `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=<port>`.
  - Electron: mit Playwright per `_electron`.
- **Start:** Debug-Build starten und nach dem Test per PID beenden. Testdaten kommen aus den Seed-Helfern oder einem eigenen Datenordner; überschreibe nie die echten Nutzerdaten des Hosts (`%APPDATA%`, `%LOCALAPPDATA%`).
- **Fenster statt Geräte, ohne Vorgabe:**
  - 1366×768
  - maximiert
  - die kleinste Fenstergröße, die die App zulässt

  Nenne die Skalierung des Hosts im Bericht. Prüfe Hell und Dunkel, wenn die App beides hat.
- **Screenshot und Struktur:** nur das App-Fenster bzw. den offenen Dialog aufnehmen (FlaUI `Capture.Element`). Struktur als Text aus dem UIA-Baum, nur so tief wie nötig: `ControlType`, `Name`, `AutomationId`, `IsEnabled`, `IsOffscreen`. UIA liefert physische Pixel; für epx durch die Skalierung des Hosts teilen.
- **Echte Bedienung:** Maus auf die Mitte des Elements (`Mouse.Click`) und Tastatur (`Keyboard`). UIA-Patterns wie `Invoke`, `Toggle` oder `SetValue` umgehen Verdeckung und Fokus: nur zum Vorbereiten, nie für den geprüften Schritt.
- **Rückmeldung:** Suche nach jeder Aktion nach neuen Fenstern (modale Dialoge, MessageBox, Benachrichtigung). Miss, wie lange die App nicht reagiert (`Process.Responding`, Fenster nicht bedienbar). Mehr als 1 s ohne Fortschrittsanzeige ist ein Befund.

## Prüfen
- **Systemeinstellungen** (Kontrastdesign, Textgröße, Skalierung) stellst du nur nach Rückfrage um und danach zurück. Ohne Erlaubnis kommen sie unter „Nicht geprüft“.
- **Tastatur:** Geh den Hauptablauf einmal nur mit der Tastatur durch. Prüfe:
  - Die Tab-Reihenfolge ist logisch, der Fokus ist sichtbar.
  - Enter löst die Standardschaltfläche aus, Esc schließt Dialoge.
  - Zugriffstasten (Alt) und übliche Kürzel (Strg+S, Strg+Z, F2, Entf) funktionieren dort, wo man sie erwartet.
- **Desktop-Konventionen:**
  - Rechtsklick öffnet ein Kontextmenü, Doppelklick öffnet ein Element.
  - Das Fenster merkt sich Größe und Position.
  - Beim Schließen mit ungespeicherten Änderungen fragt die App nach.
  - Beim Vergrößern des Fensters wächst der Inhalt mit, statt leere Fläche zu lassen.
- **Barrierefreiheit messen:**
  - bedienbare Elemente ohne `Name` im UIA-Baum (WCAG 4.1.2)
  - Kontrast aus den Pixeln des Screenshots (1.4.3, mindestens 4,5:1)
  - nur per Tastatur bedienbar (2.1.1), Fokus sichtbar (2.4.7)
  - falls das Windows SDK vorhanden ist zusätzlich `AccCheckConsole.exe -process <name>`
- **Richtwerte (Windows, Fluent):** Klickziel für die Maus mindestens 16×16 epx. Ist Touch eine Zielplattform: mindestens 40×40 epx, besser 44×44 epx mit 4 epx Abstand.
