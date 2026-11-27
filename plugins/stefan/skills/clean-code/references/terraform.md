# Terraform

Ergänzt `SKILL.md` für Terraform (`*.tf`); ersetzt dort „je Modul bzw. Klasse eine eigene Datei“.

## Struktur
- Je Umgebung ein Root-Modul (z. B. `<bereich>/<workload>/<umgebung>/`), gemeinsame Logik in `modules/<name>/` im Repo-Wurzelverzeichnis. Dateien je Modul: `terraform.tf` (`required_version`, `required_providers`), `providers.tf`, `main.tf` (wächst er: nach Bereich teilen, z. B. `network.tf`), `variables.tf`, `outputs.tf`, `locals.tf`.
- Variablen im Root-Modul nur für den Kontext, den viele Stellen brauchen (z. B. `environment`, `location`, `workload`, `tenant_id`, IDs geteilter Infrastruktur), Werte ohne Secrets als `default`. Werte der Umgebung (Adressräume, SKUs, Instanznummern, Tags, IP-Listen) stehen als Literale im Root-Modul. Namen und Tags aus dem Kontext über vorhandene Module ableiten (z. B. `naming`, `tags`), Daten geteilter Infrastruktur per `data`-Quelle lesen.
- Jede `variable` hat `type` und `description`, jeder `output` eine `description`. Secrets `sensitive = true` (stehen trotzdem im Klartext im State).
- `for_each` statt `count`, sobald Instanzen sich unterscheiden (stabile Adressen); `count` nur für an/aus.

## Versionen und Git
- Terraform, Provider und Registry-Module mit `~> X.Y`: neueste Version innerhalb der Major-Version, X.Y = kleinste benötigte (z. B. `~> 1.7`, weil `mock_provider` erst ab 1.7 geht: 1.7 bis unter 2.0). `.terraform.lock.hcl` gehört ins Repo. Provider aktualisieren mit `terraform init -upgrade` und die Lock-Datei mitcommitten; arbeiten Rechner mit anderen Betriebssystemen am Repo (z. B. CI unter Linux), `terraform providers lock -platform=linux_amd64 -platform=windows_amd64`.
- `.gitignore`: `.terraform/`, `*.tfstate*`, `*.tfplan`. Der Schutz-Hook lehnt neue State-, Plan- und `.terraform/`-Dateien ab; was ein Team-Repo schon versioniert, bleibt dessen Entscheidung.
- `*.tfvars` gehören ins Repo, aber ohne Secrets (die kommen aus Key Vault o. Ä. bzw. per `TF_VAR_*`).
- Plan immer mit `-out=<name>.tfplan`.
- Vor jedem Commit die geänderten Dateien mit `terraform fmt <datei>` formatieren (der Schutz-Hook prüft neue und geänderte Terraform-Dateien); `-recursive` nur in eigenen Repos, sonst formatiert es fremde Altdateien mit.

## TDD
- Red/Green mit `terraform test` (`tests/*.tftest.hcl`). Jeder `run`-Block mit `command = plan` oder gegen `mock_provider`: Standard ist `apply` und legt echte Infrastruktur an (der Schutz-Hook fragt dann nach).
- Prüfstufe am Ende statt Lint/Typecheck: `validate`, `tflint` (falls vorhanden) in den geänderten Modulen, `terraform test`.
- Refactor: Ressourcen oder Module nur mit `moved {}`-Block umbenennen bzw. verschieben, sonst Destroy und Neuanlage.

## Plan, Apply, Abschluss
- Vor jedem Apply `terraform plan`. Jedes `destroy`/`replace` im Plan muss gewollt sein, sonst ist es ein Befund (bei Daten Critical). Kritische Ressourcen mit `lifecycle { prevent_destroy = true }`.
- `apply`, `destroy`, `import`, `refresh`, `state rm/mv`, `init -migrate-state` nur mit Freigabe des Nutzers, nie gegen Prod im Rahmen von Tests (der Schutz-Hook fragt nach).
- Frischer Clone: `terraform init -backend=false`, dann `validate` und `terraform test`.
- Security-Review: zusätzlich `trivy config <ordner>` bzw. `checkov -f <datei>` für die geänderten Module bzw. Dateien, falls installiert.
