---
name: ui-design
description: Erstellt oder erweitert vor der Spec ein UI-Mockup im Design-Canvas des Projekts (claude.ai-Artifact, von Hand bearbeitbar) und stimmt es mit dem Nutzer ab. Verwenden, wenn Design, UI oder Aussehen einer neuen App, einer neuen Ansicht oder einer deutlich geänderten Bedienung festgelegt werden soll; nicht bei Bugfixes oder kleinen Änderungen.
---

# UI-Design

Reihenfolge: Plan (`grill-with-docs`) → **Design** → Spec (`plan-to-spec`). Ergebnis ist ein freigegebenes Mockup im Design-Canvas des Projekts, nicht im Repo. Nicht implementieren.

## Ablauf
1. **Bedarf prüfen.** Design nötig bei: neuer App, neuer Ansicht/Seite, deutlich geänderter Bedienung. Nicht nötig bei: Bugfix, reiner Backend-Änderung, Text- oder Kleinständerung, Anpassung innerhalb bestehender Komponenten → kurz sagen und abbrechen.
2. **Canvas finden.** Pro Projekt genau **ein** Canvas mit dem Projektnamen als Titel; nie einen zweiten anlegen. Suchen: `Design:`-Link in `docs/plans/` und `docs/specs/`, sonst Artifact-Liste nach Titel. Nur wenn keiner existiert: neu anlegen (Artifact-Tool `quickstart` mit `intent: design`, Typ „Design“). Immer den Anweisungen des Design-Typs folgen; vor jeder Änderung den aktuellen Stand lesen, denn der Nutzer kann von Hand geändert haben.
3. **Grundlage sammeln.** Plan aus `docs/plans/` oder Beschreibung des Nutzers; fehlt UI-relevantes Verhalten → per `AskUserQuestion` klären, eine Frage pro Aufruf. Bestehende App ohne Canvas: vorhandenes Aussehen (Theme, Farben, Schriften, Komponenten) per `Explore`-Subagent erfassen.
4. **Aussehen festlegen** – nur wenn es noch keins gibt (neue App, leerer Canvas, kein Design-System gewählt):
   - Skill `frontend-design:frontend-design` laden und seinen Design-Plan erstellen (Farben, Schrift, Layout, Prinzipien), gegen generische Standardlösungen prüfen.
   - Plan dem Nutzer kurz vorlegen und freigeben lassen, erst dann bauen.
   - Gibt es schon ein Aussehen: übernehmen, den Skill nicht laden. Einheitlichkeit geht vor Neuheit.
5. **Bauen** im Canvas:
   - Pro Plan eine eigene Seite „NNNN <Titel>“. Neue Ansichten als neue Artboards; geänderte bestehende Ansichten direkt in ihrem Artboard anpassen statt kopieren.
   - Je Zielplattform aus dem Plan eigene Artboards in deren Auflösung (z. B. Desktop 1440, iPad 1024×1366, iPhone 390×844); mobil die Bedienung anpassen (Touch-Ziele, Navigation), nicht nur verkleinern.
   - Ein Artboard pro Ansicht, wichtige Zustände (leer, viele Daten, Fehler, Dialoge) als eigene Artboards, realistische Beispieldaten.
   - Interaktiv nur so weit, dass die Bedienung erkennbar ist. Gestaltung mit den Mitteln des Ziel-Stacks (z. B. Tailwind-Werte, shadcn-Optik).
   - Bei Widersprüchen zwischen `frontend-design` und dem Design-Typ (z. B. Screenshots zur Prüfung) gilt der Design-Typ.
6. **Abstimmen.** Link zur Seite nennen, Feedback und Kommentare einarbeiten, bis der Nutzer freigibt.
7. **Festhalten.** Im Plan-Kopf ergänzen: `- **Design:** <Canvas-URL>#page-<id> (freigegeben YYYY-MM-DD)`. Ohne Plan: Link dem Nutzer nennen, `plan-to-spec` übernimmt ihn. Nächster Schritt: `plan-to-spec`.
