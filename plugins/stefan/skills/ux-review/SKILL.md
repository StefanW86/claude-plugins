---
name: ux-review
description: UX- und Usability-Review eines Ablaufs in der laufenden App aus Sicht eines Erstnutzers – Web/PWA oder Windows-Desktop (WPF, WinUI, WinForms u. a.). Die App wird per E2E-Werkzeug bedient, Befunde werden mit Screenshots belegt, nach Nielsen-Heuristiken, WCAG 2.2 AA und Plattform-Richtlinien bewertet und priorisiert. Schreibt den Bericht nach docs/ux-review/, ändert keinen Code. Nur auf ausdrücklichen Aufruf /stefan:ux-review; nicht für den Abgleich mit dem Design (das macht ui-walker in implement).
disable-model-invocation: true
argument-hint: <Ablauf, z. B. "Einkauf: abhaken und einräumen">
---

# UX-Review

Du prüfst einen Ablauf so, wie ihn ein Erstnutzer erlebt. Du änderst keinen Code.

## 1. Auftrag schärfen
- Formuliere aus dem Auftrag 1–3 **Nutzeraufgaben**, jeweils mit Ziel und Erfolgskriterium. Beispiel: „Mit vollem Wagen heimkommen und alles in den Vorrat übernehmen. Fertig, wenn die Artikel mit Menge und Lagerort im Vorrat stehen.“ Ergänze den **Nutzungskontext**: Gerät, Ort, Eingabe (Touch, Maus, Tastatur), Zeitdruck, Netz. Ist etwas unklar, stelle eine Frage per `AskUserQuestion`. Sonst triff eine Annahme und nenne sie im Bericht.
- **Plattform** aus der Projekt-`CLAUDE.md` bzw. den Projektdateien bestimmen und nur die passende Referenz lesen:
  - Web oder PWA: [references/web.md](references/web.md)
  - Windows-Desktop (`.csproj` mit `UseWPF`, `UseWindowsForms` oder Paket `Microsoft.WindowsAppSDK`, außerdem Win32, UWP, Avalonia): [references/windows.md](references/windows.md)

  Die Referenz legt Werkzeug, Geräte bzw. Fenstergrößen, Messwege und Richtwerte fest.
- **Umgebung:** lokale Instanz, Staging oder Debug-Build mit Testdaten, nie Prod. Wie die App gestartet wird, wie der Login geht und welche Testdaten es gibt, steht in der Projekt-`CLAUDE.md` bzw. der Memory.

## 2. Erleben
- Lies Code nur für Start, Login und Testdaten, nicht zur Bewertung: Was nicht sichtbar ist, kennt ein Erstnutzer nicht. Erst nach dem Erleben darf Code eine Vermutung bestätigen. Das wird im Befund gekennzeichnet.
- Schreibe ein Skript pro Gerät bzw. Fenstergröße im Scratchpad. Es führt alle Schritte aus und hält je Schritt fest:
  - einen Screenshot des sichtbaren Bereichs in Skalierung 1, also das, was der Nutzer sieht
  - die Struktur als Text, Messweg siehe Referenz

  Scheitert das Skript, führe nur die restlichen Schritte neu aus.
- Bediene die App wie ein Mensch: Tippe bzw. klicke auf das Naheliegende (Kachel, Zeile, Beschriftung), nicht gezielt auf ein verstecktes Ziel. Nutze keine Abkürzung, die die echte Eingabe umgeht (siehe Referenz). Ist ein Element verdeckt, nicht erreichbar oder nicht klickbar, ist genau das ein Befund.
- Halte die Rückmeldung direkt nach jeder Aktion fest: einen Screenshot sofort und einen nach etwa 3 s, dazu Meldungen und neue Dialoge mitschreiben. So gehen kurze Meldungen (Toasts) nicht verloren.
- Prüfe die Zustände mit, die für die Aufgaben zählen: leer, viele Einträge, Pflichtfelder leer absenden, Abbrechen bzw. Zurück, langsames oder fehlendes Netz.
- Destruktive Aktionen (Löschen, Abschließen) führst du nur bis zum Bestätigungsdialog aus und brichst dann ab. Setze geänderte Testdaten am Ende zurück oder nenne sie im Bericht.
- Beantworte für jeden Schritt vier Fragen:
  1. Weiß der Nutzer, was zu tun ist?
  2. Sieht er das Bedienelement?
  3. Bringt er es mit seinem Ziel in Verbindung?
  4. Versteht er die Rückmeldung?

## 3. Bewerten
Jeder Befund nennt eine Linse: eine der 10 Heuristiken von Nielsen (#1–#10), Informationsarchitektur, Denklast, Erwartung des Nutzers (mentales Modell), Plattform-Konvention oder WCAG 2.2 AA (gilt auch für Desktop-Software).

Priorität, streng nach diesen Kriterien:
- **Critical:** Die Aufgabe lässt sich nicht abschließen, es gehen Daten verloren, es werden falsche Daten gespeichert, oder ein **gemessener** Verstoß gegen WCAG 2.2 AA liegt vor. Nenne dann das Kriterium, z. B. 1.4.3 Kontrast < 4,5:1, 2.1.1 nicht per Tastatur bedienbar oder 2.5.8 Ziel < 24×24 px.
- **High:** Die Aufgabe gelingt, aber nur mit Umweg, Fehlversuch oder Raten; oder ein Richtwert der Plattform ist verletzt (Werte in der Referenz).
- **Enhancement:** spart Geübten Schritte oder Nachdenken.
- **Future:** neue Funktion oder größerer Umbau.

Ein unbestätigter Befund (Timing, nur im Testbrowser gesehen) bekommt höchstens High und den Vermerk „unbestätigt“. WCAG-Verstöße nur mit Messwert melden, nie nach Augenmaß. Höchstens 15 Befunde; fasse Gleichartiges zusammen.

## 4. Bericht
Schreibe den Bericht nach `docs/ux-review/<YYYY-MM-DD>-<ablauf>.md` und lege die zitierten Screenshots daneben in `docs/ux-review/<YYYY-MM-DD>-<ablauf>/`. Nichts committen. Gib den Bericht vollständig im Chat aus. Er enthält:
1. **Aufgaben, Kontext, Geräte bzw. Fenster und Skalierung:** je eine Zeile, dazu geänderte Testdaten.
2. **Erlebter Ablauf:** nummerierte Schritte, je Schritt „erwartet → passiert“.
3. **Befunde** als Tabelle, sortiert nach Priorität (Critical zuerst) und durchnummeriert:

   | # | Priorität | Befund | Vorschlag | Heuristik / Linse |
   |---|---|---|---|---|
   | 1 | **Critical** | **Einräumen speichert trotz fehlender Pflichtangabe.** Absenden geht ohne Hinweis durch; Feta landet als „1 Packung“ ohne Inhalt im Vorrat, Rezepte können ihn nicht anrechnen. Schritt 4, iPhone, `01-einraeumen.png` | Absenden sperren und das fehlende Feld markieren | #5 Fehlervermeidung, #9 Fehler erkennen |

   - **Befund:** fetter Titel als Satz, dann was passiert und was es für den Nutzer bedeutet; am Ende Schritt, Gerät bzw. Fenster und Screenshot-Datei. Höchstens 3 Sätze.
   - **Vorschlag:** die kleinste Änderung, die das Problem löst.
   - **Heuristik / Linse:** Nummer und Name, bei WCAG das Kriterium mit Messwert; „unbestätigt“ ebenfalls hier.
4. **Was gut ist** (höchstens 3 Punkte) und **Nicht geprüft / offen**.

Nenne zum Schluss den nächsten Schritt: `/stefan:implement docs/ux-review/<datei> <Nummern>`. Bei einer deutlich geänderten Bedienung ist das stattdessen `ui-design`.
