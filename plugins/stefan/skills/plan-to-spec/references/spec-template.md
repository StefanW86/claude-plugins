# Spec-Template

`<…>` ersetzen, leere Abschnitte weglassen (außer „Offene Punkte“).

## Spec: `docs/specs/NNNN-<slug>.md`

```markdown
# NNNN – Spec: <Titel>

- **Status:** Ready · **Datum:** YYYY-MM-DD
- **Quelle:** <[Plan NNNN](../plans/NNNN-<slug>.md) | Interview vom YYYY-MM-DD> · **Fortschritt:** [tasks.json](NNNN-<slug>.tasks.json)
- **Größe:** <klein|groß> (<Treffer>) → <eine Session | Orchestrator + Subagenten>
- **Umsetzung:** Skill `stefan:implement-spec` (TDD, Reviews, Abschluss), Branch `feat/NNNN-<slug>`

## 1. Umfang
<2–3 Sätze Ziel.> **Nicht im Umfang:** <Stichworte>. **User Stories, Begriffe:** <nur ohne Plan>.
**Bewusst akzeptierte Risiken:** <z. B. kein Login, nur LAN> (für das Security-Review).

## 2. Stack, Plattformen, Struktur
- <Framework + Versionen, DB/ORM, Test-Tools, UI-Lib>
- **Plattformen:** <z. B. Desktop-Web, PWA iPad/iPhone, Android/iOS nativ> · **Test-Viewports/Geräte:** <z. B. 1440×900, 1024×1366, 390×844>
- **Projektstruktur** (legt T01 an): <Ordnerbaum mit Zweck je Ordner, Ort der Tests, Namenskonventionen>

| Zweck | Befehl |
|---|---|
| Install | `<…>` |
| Dev (Port) | `<…>` |
| Alle Tests / Einzeltest | `<…>` / `<… datei>` |
| Lint / Typecheck | `<…>` / `<…>` |
| Build | `<…>` |
| E2E | `<…>` |

## 3. Datenmodell
<Schema-Ausschnitt: Felder, Typen, Pflicht, Defaults, Indizes, Relationen, Löschverhalten>

## 4. Schnittstellen
<Routen/Server Actions/Endpunkte: Eingabe, Ausgabe, Fehlerfälle>

## 5. Anforderungen
- **R-01** <prüfbares Verhalten, Edge Cases als eigene R-xx>

## 6. UI
- **Design:** <Canvas-URL#page-<id> | keins>
- **Stil:** <Farben, Schriften, Abstände/Radius, hell/dunkel>
- **Komponenten:** <Bausteine, z. B. shadcn Card, Dialog>
- **Ansichten:** <je Ansicht: Artboard `project/<name>.dc.html`, Aufbau, Interaktionen, Zustände leer/laden/Fehler>

## 7. Builder-Entscheidungen
| Thema | Entscheidung | Grund |
|---|---|---|

## 8. Tests
**Seams:** <öffentliche Schnittstellen, an denen getestet wird – möglichst hoch, möglichst wenige>.
Ebenen: Unit <…> · Integration <…> · E2E <… gegen lokale Instanz, auf allen Test-Viewports/Geräten>. Testdaten: <Isolation>.

## 9. Aufgaben
<klein: Aufgaben im Format der Aufgabendatei (unten), ohne „Kontext“.>
<groß: nur die Liste, Details in den Aufgabendateien:>
| ID | Titel | Abhängig | Datei |
|---|---|---|---|
| T01 | <…> | – | [T01](NNNN-<slug>/T01.md) |

## 10. Offene Punkte
keine
```

## Aufgabendatei (nur groß): `docs/specs/NNNN-<slug>/Txx.md`

Eigenständig: enthält **nur**, was für diese Aufgabe nötig ist, und genug, um sie ohne Spec zu lösen. Was frühere Aufgaben schon gebaut haben, als Pfad im Code referenzieren statt kopieren.

```markdown
# Txx – <Titel>

**Ziel:** <lauffähiges Inkrement>

## Kontext
- Stack: <nur Relevantes>, betroffene Ordner, Seam für diese Aufgabe. Befehle: Einzeltest `<…>`, alle Tests `<…>`, Lint `<…>`, Typecheck `<…>`
- Vorhanden aus früheren Aufgaben: <z. B. `prisma/schema.prisma` (T02), `lib/db.ts`>
- Anforderungen: **R-xx** <Volltext> …
- Datenmodell/Schnittstellen: <nur betroffene Ausschnitte>
- Entscheidungen: <nur relevante Builder-Entscheidungen>
- UI (nur UI-Aufgaben): <Ansicht, Stil, Komponenten aus Spec-Abschnitt 6>; Design: <Canvas-URL>, Artboard `project/<name>.dc.html`

## Dateien
`<anzulegen/zu ändern>`

## Testfälle
- [ ] <Ebene>: Angenommen <…>, wenn <…>, dann <…>
- [ ] <nur UI-Aufgaben> Visuell, je Test-Viewport: eigener Screenshot entspricht in Aufbau, Stil und Zuständen dem Artboard (nur dieses per Artifact-Tool `read` mit `path` holen)

## Hinweise
<nur Fallstricke>
```

## tasks.json
```json
{"spec": "docs/specs/NNNN-<slug>.md", "mode": "small|large", "tasks": [
  {"id": "T01", "title": "<…>", "dependsOn": [], "requirements": ["R-01"], "model": "sonnet|opus", "status": "todo", "commit": null, "notes": ""}
]}
```
`status`: todo → in_progress → done | blocked (Grund in `notes`). `model` nur bei `large`.
