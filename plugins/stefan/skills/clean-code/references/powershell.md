# PowerShell

Ergänzt `SKILL.md` für Skripte, Module und Runbooks (`*.ps1`, `*.psm1`, `*.psd1`). Projektregeln und der Stil einer bestehenden Datei gehen vor.

## Namen und Aufbau
- Code, Kommentare und Ausgaben auf Englisch. Funktionen `Verb-Noun` mit zugelassenem Verb (`Get-Verb`), keine Aliase, Parameter mit Namen statt Position.
- Kopf: Comment-based Help (`.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE`, `.NOTES` mit `Author:` aus `git config user.name`/`user.email` des Projekts und `Version:`), darunter `#Requires -Version 7.2` bzw. `5.1`, bei Bedarf `#Requires -Modules`.
- `[CmdletBinding()]` und `param()` mit Typen und Validierung (`[Parameter(Mandatory)]`, `[ValidateSet()]`, `[ValidateNotNullOrEmpty()]`). Parameter nur für Werte, die je Umgebung oder Aufruf abweichen, mit sicherem Standardwert.

## Fehler
- `$ErrorActionPreference = 'Stop'`, `try`/`catch`/`finally`; aufräumen im `finally` (`Dismount-VHD`, temporäre Dateien, Verbindungen).
- Native Programme: `$LASTEXITCODE` prüfen. Leerer `catch` nur mit begründendem Kommentar.
- Erfolgsmeldung erst am Ende, nachdem das Ergebnis geprüft wurde.

## Sicherheit
- Geringste nötige Rechte, Eingaben validieren. Secrets aus Umgebungsvariablen, `SecretManagement`, Automation Credentials oder Key Vault; in Ausgaben und Logs maskieren.
- Riskante Änderungen: `[CmdletBinding(SupportsShouldProcess)]` und `$PSCmdlet.ShouldProcess()`, Löschen mit `ConfirmImpact = 'High'`. Massenlöschung oder umfassende Änderung zusätzlich standardmäßig Dry Run, ausgeführt erst mit `-Execute`.
- Kein `Invoke-Expression` mit fremden Eingaben, kein Code aus ungeprüften Quellen.

## Ausgabe
- Ergebnisse als Objekte über die Pipeline; Status per `Write-Verbose`, `Write-Information`, `Write-Warning`. `Write-Host` nur für reine Anzeige.
- Funktionen geben nur ihr Ergebnis zurück: `Write-Output` für Logzeilen landet im Rückgabewert.

## Fallen
- Ein Ein-Element-Array wird zum Skalar: Rückgaben und `$x = if (...) {...}` mit `@()` umschließen.
- `New-Item -Force` auf einen vorhandenen Registry-Schlüssel leert ihn; Werte mit `Set-ItemProperty` setzen.
- 5.1 liest Dateien ohne BOM als ANSI: Skripte für 5.1 reines ASCII oder UTF-8 mit BOM (der Schutz-Hook lehnt den Commit sonst ab).
- 5.1: natives Programm mit `2>&1` unter `ErrorActionPreference = 'Stop'` wirft einen Fehler.
- Here-Strings aus Windows enthalten CRLF; für Linux vorher `sed -i 's/\r$//'`.
- Umlaute auf der Konsole können unter cp1252 scheitern; dann in eine Datei schreiben.

## Module und Azure
- Benötigte Module installiert die Bereitstellung (`Install-PSResource -Scope AllUsers -TrustRepository -Quiet`), nie jemand von Hand.
- Azure-Aufrufe bei vorübergehenden Fehlern wiederholen (Helper `Invoke-WithRetry`).
- Runbooks: Managed Identity, beginnen mit `Disable-AzContextAutosave`; die 3-Stunden-Grenze von Azure Automation beachten und Folge-Jobs starten.

## TDD und Prüfung
- Red/Green mit Pester 5 (`tests/*.Tests.ps1`, `Invoke-Pester -Output Detailed`). `Mock` nur an Systemgrenzen (Az-Cmdlets, Dateisystem, Registry, Zeit), nie gegen echte Ressourcen.
- Prüfstufe am Ende statt Lint/Typecheck: `Invoke-ScriptAnalyzer -Path . -Recurse` ohne Befunde, Formatierung per `Invoke-Formatter -Settings CodeFormattingOTBS`, Pester. Fehlen PSScriptAnalyzer oder Pester: `Install-PSResource -Scope CurrentUser`.
- Skripte für 5.1 mit `powershell.exe` prüfen, nicht mit `pwsh`. Ohne Windows-Host sagen, dass 5.1 ungeprüft ist.
