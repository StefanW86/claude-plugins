# claude-plugins

Marketplace `stefan-local` mit zwei Plugins:

| Plugin | Inhalt | Installieren auf |
|---|---|---|
| `stefan` | Entwicklungsablauf (Skills, Agents), Schutz-Hook, Session-Statistik | allen Rechnern |
| `stefan-homelab` | Schutz der Prod-Checkouts, Konventionen für neue Apps | nur dem Homelab (Linux) |

Ab Version 2.0.0 von `stefan` liegen Prod-Schutz und `deploy-neue-app` in `stefan-homelab`: auf dem Homelab zusätzlich installieren.

## Ablauf (Plugin stefan)

`/stefan:go` führt durch alle Phasen und setzt nach Unterbrechungen an der richtigen Stelle fort:

1. **Plan** – `grill-with-docs`: Interview mit einer Frage pro Runde, Ergebnis `docs/plans/NNNN-<slug>.md`.
2. **Design** (nur bei neuer UI) – `ui-design`: Mockup im Design-Canvas des Projekts.
3. **Spec** – `plan-to-spec`: Anforderungen, Aufgaben mit Testfällen, Größe klein oder groß, Ergebnis in `docs/specs/`.
4. **Umsetzung** – `implement`: TDD je Aufgabe, im Modus groß mit Subagenten (`task-implementer`, `task-reviewer`). Abschluss mit Diät (`simplify`), Code- und Security-Review, `ui-walker` (bei UI), `closing-checker`, Bericht und Integration.

Außerdem:
- `/stefan:go-quick`: kurz klären, dann direkt umsetzen nach `clean-code`, ohne TDD.
- `implement` im Modus Direkt: Bugfixes und kleine Änderungen ohne Spec, außerdem Befunde aus Berichten (`implement <bericht> [Nummern]`, ohne Nummern alle offenen). Der Bearbeitungsstand steht im Bericht selbst: Spalte „Status“, Folgepunkte aus der Umsetzung, nächster Schritt; `/stefan:go` erkennt offene Berichte.
- `/stefan:audit`: Qualitätsbericht nach `docs/audit/`, ändert keinen Code. Nur per Befehl, Claude startet ihn nicht selbst.
- `/stefan:ux-review <Ablauf>`: UX-Review eines Ablaufs aus Sicht eines Erstnutzers (Web/PWA, Windows-Desktop), Bericht nach `docs/ux-review/`, ändert keinen Code. Nur per Befehl, Claude startet ihn nicht selbst.
- `clean-code`: Regeln für Code und Tests, dazu Terraform und PowerShell.
- `/stefan:session-stats`: Kosten, Tokens und Zeiten der Session (Mod).

### Angaben in der Projekt-CLAUDE.md

- `Integration: <basis>, merge|mr`: Basis-Branch und Weg nach der Abnahme. `merge` heißt lokal mergen und pushen, `mr` heißt Branch pushen und Merge Request bzw. Pull Request anlegen. Fehlt die Zeile, fragt `implement` einmal und trägt sie ein.
- Befehle, E2E-Weg und bei UI Vorschau-Weg und Test-Geräte; das legt `plan-to-spec` an. Projekte ohne UI (Terraform, PowerShell) testen E2E auf oberster Ebene, z. B. mit `terraform test` oder Pester.
- Optional ein Branch-Schema, sonst `feature/…` bzw. `fix/…`.

## Schutz-Hook (Plugin stefan)

Prüft Bash- und PowerShell-Aufrufe vor der Ausführung:

| Regel | Folge |
|---|---|
| Prozesse nach Namen beenden (`pkill`, `killall`, `kill $(pgrep …)`, `Stop-Process -Name`, `taskkill /IM`) | abgelehnt |
| Commit direkt auf `main`/`master` (außer erstem Commit, Merge-Abschluss und Branchwechsel im selben Befehl) | abgelehnt |
| Commit mit `Co-Authored-By`, auch aus einer Nachrichtendatei (`-F`) | abgelehnt |
| Commit mit neuen State-, Plan- oder `.terraform/`-Dateien | abgelehnt |
| Commit mit geänderten Terraform-Dateien, die `terraform fmt -check` nicht bestehen | abgelehnt |
| Commit mit geänderten PowerShell-Skripten mit Nicht-ASCII ohne BOM (außer nur für PowerShell 7) | abgelehnt |
| `terraform apply`, `destroy`, `import`, `refresh`, `state rm/mv`, `init -migrate-state`; `terraform test` mit echter Infrastruktur | Rückfrage |

Die Commit-Prüfungen gelten nur für neue und geänderte Dateien, die der Commit enthält (Index, `git add` davor im selben Befehl, `commit -a`, Pfade beim Commit); nicht gestagte Änderungen und ungetrackte Dateien bleiben außen vor. Was unverändert im Repo liegt, etwa Altskripte in Team-Repos, hat das Projekt entschieden.

Unter Windows merkt sich der Hook den Pfad zu Python, ein Aufruf dauert dann rund 0,3 s. Fehlt Python, laufen die Tools mit einer Warnung ohne Prüfung weiter.

## Plugin stefan-homelab

- **Schutz-Hook:** Git-Repos direkt unter `$HOME` (außer `*-work` und Punktordnern) sind Prod-Checkouts, die nur der Deploy ändert. Edit und Write dort werden abgelehnt (außer `.env`), ebenso Git-Änderungen; andere Schreibbefehle brauchen eine Rückfrage.
- **Skill `deploy-neue-app`:** Konventionen für neue Apps (Docker Compose, cloudflared, `swdhomelab/deploy`).

## Voraussetzungen

- Claude Code ab v2.1.275
- Python 3 für die Hooks
- Windows zusätzlich Git for Windows (für `sh`), z. B. `winget install Git.Git Python.Python.3.13`
- Für `ui-design` das Plugin `frontend-design` aus dem offiziellen Marketplace:
  ```text
  /plugin marketplace add anthropics/claude-plugins-official
  /plugin install frontend-design@claude-plugins-official
  ```

## Terminal (Claude Code CLI)

### Installieren

In der Shell:

```sh
claude plugin marketplace add StefanW86/claude-plugins
claude plugin install stefan@stefan-local
claude plugin install stefan-homelab@stefan-local   # nur auf dem Homelab
```

Oder in einer laufenden Session:

```text
/plugin marketplace add StefanW86/claude-plugins
/plugin install stefan@stefan-local
/plugin install stefan-homelab@stefan-local
```

Die letzte Zeile nur auf dem Homelab. Danach Session neu starten oder `/reload-plugins` ausführen.

### Aktualisieren

```sh
claude plugin marketplace update stefan-local
claude plugin update stefan@stefan-local
claude plugin update stefan-homelab@stefan-local   # nur auf dem Homelab
```

Danach Session neu starten oder `/reload-plugins`.
Alternativ in der Session: `/plugin` → Tab **Marketplaces** → `stefan-local` → **Update marketplace**.

Automatisch aktualisieren (standardmäßig aus): `/plugin` → **Marketplaces** → `stefan-local` → Auto-Update einschalten.

## Windows Desktop App (Claude Code)

Desktop App und CLI teilen sich auf einem Rechner `~/.claude`. Ist das Plugin per Terminal mit
User-Scope installiert, ist es in der Desktop App schon da – und umgekehrt.
Die PowerShell-Befehle unten brauchen die CLI (`irm https://claude.ai/install.ps1 | iex`).

### Installieren

1. In der Desktop App Tab **Code** öffnen und eine lokale Session starten.
2. Marketplace hinzufügen – im Eingabefeld:
   ```text
   /plugin marketplace add StefanW86/claude-plugins
   ```
   Alternativ in PowerShell: `claude plugin marketplace add StefanW86/claude-plugins`
3. Plugin installieren: **+** neben dem Eingabefeld → **Add plugins**
   (bzw. **Plugins** → **Browse plugins**) → `stefan` wählen → Scope **User** wählen.
   Alternativ im Eingabefeld: `/plugin install stefan@stefan-local`
4. Neue Session starten.

### Aktualisieren

In PowerShell:

```powershell
claude plugin marketplace update stefan-local
claude plugin update stefan@stefan-local
```

Alternativ im Eingabefeld einer Code-Session: `/plugin` → Tab **Marketplaces** → `stefan-local` →
**Update marketplace** (aktualisiert auch das installierte Plugin).

Danach neue Session starten oder `/reload-plugins`.

## Tests

```sh
python -m unittest discover tests
```

Die Tests mit `terraform fmt` laufen nur, wenn `terraform` im PATH liegt; sonst werden sie übersprungen.
GitHub Actions führt alle Tests unter Ubuntu und Windows aus. `shellparse.py` liegt in beiden Plugins
in identischer Kopie, ein Test prüft das.
