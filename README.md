# claude-plugins

Marketplace `stefan-local` mit dem Plugin `stefan` (Skills, Agents, Schutz-Hook).

## Voraussetzungen

- Claude Code ab v2.1.275
- Python 3 (der Schutz-Hook läuft in Python)
- Windows zusätzlich: Git for Windows (für `sh`) und Python 3, z. B.
  `winget install Git.Git Python.Python.3.13`

## Terminal (Claude Code CLI)

### Installieren

In der Shell:

```sh
claude plugin marketplace add StefanW86/claude-plugins
claude plugin install stefan@stefan-local
```

Oder in einer laufenden Session:

```text
/plugin marketplace add StefanW86/claude-plugins
/plugin install stefan@stefan-local
```

Danach Session neu starten oder `/reload-plugins` ausführen.

### Aktualisieren

```sh
claude plugin marketplace update stefan-local
claude plugin update stefan@stefan-local
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
