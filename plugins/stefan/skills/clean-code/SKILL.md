---
name: clean-code
description: Wendet KISS, DRY und YAGNI an, wenn Code geschrieben, refaktoriert oder reviewt wird. Verwenden bei neuen Features, Refactorings, Code-Reviews oder wenn der Nutzer nach einfacherem bzw. saubererem Code fragt.
---

# KISS, DRY, YAGNI

## KISS – Keep It Simple
- Nimm die einfachste Lösung, die die Anforderung erfüllt.
- Keine Abstraktionsschichten, Patterns oder generischen Frameworks ohne konkreten Bedarf.
- Kurze Funktionen mit einer Aufgabe und sprechenden Namen.
- Lesbarkeit geht vor Cleverness.
- je Modul, Klasse eigene Codedatei

## DRY – Don't Repeat Yourself
- Gleiche Logik, die an 3 oder mehr Stellen vorkommt, wird extrahiert.
- Konstanten und Konfiguration haben eine einzige Quelle.
- Code, der nur zufällig gleich aussieht, wird nicht zusammengelegt. Nicht über-abstrahieren.

## YAGNI – You Aren't Gonna Need It
- Setze nur um, was aktuell verlangt ist.
- Keine „für später“-Parameter, Feature-Flags, Plugin-Systeme oder ungenutzten Interfaces.
- Keine spekulative Konfigurierbarkeit.

## Vorgehen
1. Vor dem Coden: Was ist die minimale Lösung?
2. Nach dem Coden: Gibt es Duplikate, unnötige Abstraktionen oder ungenutzten Code? Dann entfernen.
3. Wenn Du bewusst von einem Prinzip abweichst, begründe es kurz.
