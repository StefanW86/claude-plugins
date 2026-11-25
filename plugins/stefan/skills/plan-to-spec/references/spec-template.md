# Spec-Template

`<…>` ersetzen, leere Abschnitte weglassen (außer „Offene Punkte“).

## Spec: `docs/specs/NNNN-<slug>.md`

```markdown
# NNNN – Spec: <Titel>

- **Status:** Ready · **Datum:** YYYY-MM-DD
- **Quelle:** <[Plan NNNN](../plans/NNNN-<slug>.md) | Interview vom YYYY-MM-DD> · **Fortschritt:** [tasks.json](NNNN-<slug>.tasks.json)
- **Größe:** <klein|groß> (<Treffer>) → <eine Session | Orchestrator + Subagenten>
- **Umsetzung:** Skill `stefan:implement` (TDD, Reviews, Abschluss), Branch nach Projektschema, sonst `feature/NNNN-<slug>` (letzter Namensteil `NNNN-<slug>` oder `<slug>`)
- **Vorab vom Nutzer:** <nur was Claude nicht selbst kann, mit Ort, z. B. Secret `DEPLOY_DISPATCH_TOKEN` im App-Repo, `TUNNEL_TOKEN` in Prod-`.env` | keine>

## 1. Umfang
<2–3 Sätze Ziel.> **Nicht im Umfang:** <Stichworte>. **User Stories, Begriffe:** <nur ohne Plan>.
**Bewusst akzeptierte Risiken:** <z. B. kein Login, nur LAN> (für das Security-Review).

## 2. Stack, Plattformen, Struktur
- <Framework + Versionen, DB/ORM, Test-Tools, UI-Lib>
- Ohne UI: **Zielsysteme:** <z. B. Windows Server 2022 mit PowerShell 5.1, Azure Automation, Terraform ≥ 1.7 gegen Azure>
- Mit UI: **Plattformen:** <z. B. Desktop-Web, PWA iPad/iPhone, Android/iOS nativ> · **Test-Geräte:** <je Plattform ein Gerät bzw. Profil im E2E-Werkzeug, mobil mit Touch und passender Engine, z. B. Desktop 1440×900, iPhone-Profil mit WebKit, Windows 1920×1080; Desktop-App (z. B. .NET WPF/WinForms/WinUI) per UI-Automation-Werkzeug wie FlaUI oder Appium; hat die App Hell/Dunkel, beide Themes>
- **Projektstruktur** (legt T01 an): <Ordnerbaum mit Zweck je Ordner, Ort der Tests, Namenskonventionen>

| Zweck | Befehl |
|---|---|
| Install | `<…>` |
| Dev (Port) | `<…>` |
| Alle Tests / Einzeltest | `<…>` / `<… datei>` |
| Lint / Typecheck | `<…>` / `<…>` |
| Build | `<…>` |
| E2E | `<…>` |
| Prüfen: Lint, Typecheck, Unit, E2E in einem Aufruf, nur Fehler und Zusammenfassung | `<…>` |

## 3. Datenmodell
<Schema-Ausschnitt: Felder, Typen, Pflicht, Defaults, Indizes, Relationen, Löschverhalten>

## 4. Schnittstellen
<Routen/Server Actions/Endpunkte: Eingabe, Ausgabe, Fehlerfälle>

## 5. Anforderungen
- **REQ-01** <prüfbares Verhalten, Edge Cases als eigene REQ-xx>

## 6. UI
- **Design:** <Canvas-URL#page-<id> | keins>
- **Stil:** <Farben, Schriften, Abstände/Radius, hell/dunkel>
- **Komponenten:** <legt der Stack eine UI-Bibliothek fest: jedes Bedienelement → ihre Komponente (Datum, Auswahl, Dialog …); sonst die gewählten Bausteine>
- **Ansichten:** <je Ansicht: Artboard `project/<name>.dc.html`, Aufbau, Interaktionen (welche Fläche auf Klick/Tap/Ziehen reagiert), Zustände leer/laden/Fehler/geöffnet>

## 7. Builder-Entscheidungen
| Thema | Entscheidung | Grund |
|---|---|---|

## 8. Tests
**Seams:** <öffentliche Schnittstellen, an denen getestet wird – möglichst hoch, möglichst wenige>.
Ebenen: Unit <…> · Integration <…> · E2E <mit UI: gegen lokale Instanz auf allen Test-Geräten; ohne UI: Test auf oberster Ebene, z. B. `terraform test`, Pester>. Testdaten: <Isolation>.

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
- Anforderungen: **REQ-xx** <Volltext> …
- Datenmodell/Schnittstellen: <nur betroffene Ausschnitte>
- Entscheidungen: <nur relevante Builder-Entscheidungen>
- UI (nur UI-Aufgaben): <Ansicht, Stil, Komponenten aus Spec-Abschnitt 6>; Design: <Canvas-URL>, Artboard `project/<name>.dc.html`

## Dateien
`<anzulegen/zu ändern>`

## Testfälle
- [ ] <Ebene>: Angenommen <…>, wenn <…>, dann <…>
- [ ] <nur nutzersichtbare Aufgaben> E2E: <Ablauf aus Nutzersicht mit realistischer Geste, z. B. Klick neben den Titel, Ziehen nur ¼ ins Ziel, Tap auf iPhone>
- [ ] <nur UI-Aufgaben> Visuell, je Test-Gerät und Theme: eigener Screenshot inkl. geöffneter Elemente (Menü, Picker, Dialog) entspricht in Aufbau, Stil und Zuständen dem Artboard (nur dieses per Artifact-Tool `read` mit `path` holen)

## Hinweise
<nur Fallstricke>
```

## tasks.json
```json
{"spec": "docs/specs/NNNN-<slug>.md", "mode": "small|large", "tasks": [
  {"id": "T01", "title": "<…>", "dependsOn": [], "requirements": ["REQ-01"], "model": "sonnet|opus", "status": "todo", "commit": null, "notes": ""}
], "closing": {"status": "todo", "notes": ""}}
```
`status`: todo → in_progress → done | blocked (wartet auf den Nutzer, Grund in `notes`). `closing`: todo → done nach Abschluss und Bericht, `notes` = Kurzbericht für die Abnahme. `model` nur bei `large`.
