---
name: go-quick
description: Schneller Weg ohne Prozess – kurz Verständnis klären, dann direkt umsetzen wie ohne Plugin, nur nach KISS, DRY und YAGNI. Verwenden bei /go-quick.
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
Direkt umsetzen, wie Claude es ohne dieses Plugin täte.
- Keine Spec, kein Design, kein `stefan:implement`, keine Reviews oder Subagenten.
- `stefan:clean-code` nicht laden: TDD, Testregeln, Prüfstufen und UI-Regeln gelten hier nicht. Tests nur, wenn der Nutzer sie verlangt oder vorhandene Tests durch die Änderung brechen.
- Es gelten nur:
  - **KISS:** die einfachste Lösung, die funktioniert.
  - **DRY:** Vorhandenes suchen und wiederverwenden; dieselbe Regel nur an einer Stelle.
  - **YAGNI:** nur das Verlangte, nichts „für später“.
- Git wie immer: Branch von main, nach Abnahme Merge und Push.
