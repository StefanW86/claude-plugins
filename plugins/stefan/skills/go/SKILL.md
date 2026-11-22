---
name: go
description: Führt durch den gesamten Entwicklungsprozess von der Idee bis zum Merge – Plan, Design (falls nötig), Spec, Umsetzung mit Reviews – und setzt nach Unterbrechungen an der richtigen Stelle fort. Verwenden bei /go oder wenn ein Feature oder Projekt komplett durchgezogen werden soll.
disable-model-invocation: true
---

# Go

Verkettet die Phasen-Skills. Jede Phase lädt ihren Skill per Skill-Tool und folgt ihm. Nach dem Freigabepunkt geht es ohne Empfehlungsschritt direkt mit der nächsten Phase weiter. Zwischen den Phasen nur eine Zeile Status („Plan steht → weiter mit Design“).

## Einstieg bestimmen (bei jedem Aufruf)
- **Mit Idee als Argument:** neue Arbeit bei Phase 1. Läuft schon eine unfertige Arbeit, kurz fragen: fortsetzen oder neu beginnen.
- **Ohne Argument:** die neueste unfertige Arbeit in `docs/plans/` und `docs/specs/` suchen (gleiche Nummer = gleiche Arbeit) und einsteigen:

| Zustand | Phase |
|---|---|
| nichts gefunden | nach der Idee fragen → 1 |
| Plan, Design nötig (Kriterien in `stefan:ui-design`), keine Design-Seite | 2 Design |
| Plan ohne Spec | 3 Spec |
| Spec `Ready` oder `In Progress` | 4 Umsetzung |
| alle Specs `Done` | nichts offen → nach neuer Idee fragen |

## Phasen und Freigabepunkte
1. **Plan:** `stefan:grill-with-docs`. Freigabe: Bestätigung am Ende des Interviews. Bugfix oder kleine Änderung (ein Bereich, wenige Dateien) → direkt `stefan:implement` im Modus Direkt, ohne Spec. Mittleres Feature → Phase 1 und 2 überspringen, Phase 3 ohne Plan (kurzes Interview).
2. **Design** (nur wenn nötig): `stefan:ui-design`. Freigabe: Mockup vom Nutzer freigegeben.
3. **Spec:** `stefan:plan-to-spec`. Freigabe per `AskUserQuestion`:
   - „Freigeben, frische Session (Recommended)“: Planung belastet den Kontext der Umsetzung nicht. Der Nutzer führt `/clear` aus, dann `/stefan:go`.
   - „Freigeben, hier weiter“: direkt Phase 4.
   - „Änderungen“: einarbeiten, erneut fragen.
4. **Umsetzung:** `stefan:implement`. Freigabe: Abnahme durch den Nutzer, dann Merge und Push.
