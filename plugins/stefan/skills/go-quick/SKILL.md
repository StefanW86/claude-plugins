---
name: go-quick
description: Schneller Weg ohne Prozess – kurz Verständnis klären, dann direkt umsetzen nach den Regeln aus clean-code, ohne TDD und mit minimaler Prüfung. Verwenden bei /go-quick.
disable-model-invocation: true
---

# Go-quick

## 1. Verständnis klären
Fragen, bis Ziel, Verhalten und Grenzen der Aufgabe klar sind, nach den Regeln aus `stefan:grill-with-docs` (Skill nicht laden):
- **Genau eine Frage pro Runde** per `AskUserQuestion`, Empfehlung zuerst. Immer die Frage, deren Antwort am meisten vom Rest bestimmt; vage oder widersprüchliche Antworten zuerst klären.
- **Fakten selbst nachsehen, Entscheidungen fragen:** Code, Dateien und Docs selbst lesen statt danach zu fragen.
- **Mit Szenarien prüfen:** konkrete Randfälle nennen, die die Grenzen festlegen; unscharfe Begriffe schärfen.
- Nur fragen, was die Umsetzung ändert. Keine Pflichtthemen, kein Plan-Dokument. Ist alles klar oder die Aufgabe eindeutig, keine Fragen.
- Zum Schluss Entscheidungen in wenigen Zeilen zusammenfassen, ohne Rückfrage direkt loslegen.

## 2. Umsetzen
Direkt umsetzen: keine Spec, kein Design, kein `stefan:implement`, keine Reviews oder Subagenten.
- Zu Beginn Skill `stefan:clean-code` laden und befolgen, außer den Abschnitten „TDD“ und „Prüfstufen“.
- Tests nur, wenn der Nutzer sie verlangt oder vorhandene Tests durch die Änderung brechen.
- Einmal am Ende das Nötigste prüfen: vorhandene Tests der geänderten Bereiche per Dateifilter, dazu Lint bzw. Typecheck, falls vorhanden. E2E nur, wenn sonst nichts die Änderung abdeckt, dann nur diese Datei auf einem Gerät. Keine Gesamtsuite, kein frischer Clone, keine Vorschau, außer auf Wunsch. Im Bericht sagen, was geprüft ist und was nicht.
- Git: Branch nach dem Schema aus `CLAUDE.md` (sonst `feature/<slug>` bzw. `fix/<slug>`) vom Basis-Branch aus der Zeile `Integration: <basis>, merge|mr` der Projekt-`CLAUDE.md` (fehlt sie: `main`, `merge`). Nach Abnahme bei `merge` mergen und pushen, bei `mr` den Branch pushen und einen Merge Request bzw. Pull Request anlegen.
