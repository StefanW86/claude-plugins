---
name: go-quick
description: Schneller Weg ohne Prozess – direkt umsetzen wie ohne Plugin, nur nach KISS, DRY und YAGNI. Verwenden bei /go-quick.
disable-model-invocation: true
---

# Go-quick

Die Aufgabe aus dem Argument direkt umsetzen, wie Claude es ohne dieses Plugin täte.

- Kein Plan, keine Spec, kein Design, kein `stefan:implement`, keine Reviews oder Subagenten.
- `stefan:clean-code` nicht laden: TDD, Testregeln, Prüfstufen und UI-Regeln gelten hier nicht. Tests nur, wenn der Nutzer sie verlangt oder vorhandene Tests durch die Änderung brechen.
- Es gelten nur:
  - **KISS:** die einfachste Lösung, die funktioniert.
  - **DRY:** Vorhandenes suchen und wiederverwenden; dieselbe Regel nur an einer Stelle.
  - **YAGNI:** nur das Verlangte, nichts „für später“.
- Git wie immer: Branch von main, nach Abnahme Merge und Push.
