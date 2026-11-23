# PowerShell

Ergänzt `SKILL.md` für Skripte, Module und Runbooks (`*.ps1`, `*.psm1`, `*.psd1`). Projektregeln gehen vor, ebenso der Stil einer bestehenden Datei (Formatierung, Benennung, Sprache); Mängel darin werden nicht übernommen.

## Namen und Aufbau
- Code, Kommentare und Ausgaben auf Englisch. Funktionen `Verb-Noun` mit zugelassenem Verb (`Get-Verb`), keine Aliase, Parameter mit Namen statt Position.
- Kopf: Comment-based Help (`.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE`, `.NOTES` mit `Author:` aus `git config user.name`/`user.email` des Projekts und `Version:`), darunter `#Requires -Version 7.2` bzw. `5.1`, bei Bedarf `#Requires -Modules @{ ModuleName = '<Modul>'; ModuleVersion = 'X.Y' }`.
- `[CmdletBinding()]` und `param()` mit Typen und Validierung (`[Parameter(Mandatory)]`, `[ValidateSet()]`, `[ValidateNotNullOrEmpty()]`); optionale Parameter mit sicherem Standardwert.

## Fehler
- `$ErrorActionPreference = 'Stop'`, `try`/`catch`/`finally`; aufräumen im `finally` (`Dismount-VHD`, temporäre Dateien, Verbindungen).
- Native Programme: `$LASTEXITCODE` prüfen. Kein leerer `catch`: einen bewusst ignorierten Fehler per `Write-Verbose` mit Grund vermerken.
- Erfolgsmeldung erst am Ende, nachdem das Ergebnis geprüft wurde.

## Sicherheit
- Geringste nötige Rechte, Eingaben validieren. Secrets aus Umgebungsvariablen, `SecretManagement`, Automation Credentials oder Key Vault; in Ausgaben und Logs maskieren.
- Funktionen mit ändernden Verben (`New`, `Set`, `Remove`, `Start`, `Stop`, `Restart`, `Reset`, `Update`): `[CmdletBinding(SupportsShouldProcess)]` und `$PSCmdlet.ShouldProcess()`, Löschen mit `ConfirmImpact = 'High'`. Massenlöschung oder umfassende Änderung zusätzlich standardmäßig Dry Run, ausgeführt erst mit `-Execute`.
- Kein `Invoke-Expression` mit fremden Eingaben, kein Code aus ungeprüften Quellen.

## Ausgabe
- Ergebnisse als Objekte über die Pipeline; Status per `Write-Verbose`, `Write-Information`, `Write-Warning`. `Write-Host` nur für reine Anzeige.
- Funktionen geben nur ihr Ergebnis zurück: `Write-Output` für Logzeilen landet im Rückgabewert.

## Fallen
- Ein Ein-Element-Array wird zum Skalar: beim Aufrufer mit `@()` umschließen (`@(Get-Thing)`, `$x = @(if (...) {...})`); `return @($x)` in der Funktion hilft nicht.
- `New-Item -Force` auf einen vorhandenen Registry-Schlüssel leert ihn; Werte mit `Set-ItemProperty` setzen.
- 5.1 liest Dateien ohne BOM als ANSI: Skripte für 5.1 reines ASCII oder UTF-8 mit BOM (der Schutz-Hook lehnt den Commit sonst ab).
- 5.1: natives Programm mit `2>&1` unter `ErrorActionPreference = 'Stop'` wirft einen Fehler.
- Here-Strings aus Windows enthalten CRLF; für Linux vorher `sed -i 's/\r$//'`.
- Umlaute auf der Konsole können unter cp1252 scheitern; dann in eine Datei schreiben.

## Module und Azure
- Modulversionen: neueste innerhalb der Major-Version (`-Version '[X.Y,<X+1>.0)'`, im Kopf `ModuleVersion = 'X.Y'`).
- Auf Zielsystemen installiert die Bereitstellung die Module (`Install-PSResource -Scope AllUsers -TrustRepository -Quiet`), nie jemand von Hand. Lokal fehlende Module (Abhängigkeiten, PSScriptAnalyzer, Pester) ohne Rückfrage installieren: `Install-PSResource -Scope CurrentUser -TrustRepository -Quiet`, Pester mit `-Version '[5.0,6.0)'`; für 5.1 in `powershell.exe` (eigener Modulpfad) `Install-Module -Scope CurrentUser -Force`, Pester zusätzlich `-MaximumVersion 5.99 -SkipPublisherCheck`.
- Azure-Aufrufe bei vorübergehenden Fehlern wiederholen (Helper `Invoke-WithRetry`).
- Runbooks: Managed Identity, beginnen mit `Disable-AzContextAutosave`; Funktionen mit `ConfirmImpact = 'High'` mit `-Confirm:$false` aufrufen (die Sandbox kann nicht nachfragen); die 3-Stunden-Grenze von Azure Automation beachten und Folge-Jobs starten.

## TDD und Prüfung
- Red/Green mit Pester 5 (`tests/*.Tests.ps1`, `Invoke-Pester -Output Detailed`). `Mock` für Az-Cmdlets und Zeit; Dateien und Registry über `TestDrive:` bzw. `TestRegistry:` (nur Windows); nie gegen echte Ressourcen.
- Prüfstufe am Ende statt Lint/Typecheck: `Invoke-ScriptAnalyzer -Path . -Recurse` ohne Befunde, Pester.
- Was diese Regeln erlauben, der Analyzer aber meldet (z. B. `Write-Host` zur Anzeige, Nicht-ASCII ohne BOM bei `#Requires -Version 7.2`): `[Diagnostics.CodeAnalysis.SuppressMessageAttribute('<Regel>', '', Justification = '<Grund>')]` bzw. projektweit in `PSScriptAnalyzerSettings.psd1`.
- Neue Dateien mit `Invoke-Formatter -Settings CodeFormattingOTBS` formatieren, bestehende im vorhandenen Stil lassen.
- Skripte für 5.1 mit `powershell.exe` prüfen, nicht mit `pwsh`. Ohne Windows-Host sagen, dass 5.1 ungeprüft ist.
