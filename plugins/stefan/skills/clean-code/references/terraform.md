# Terraform

Ergänzt `SKILL.md` für Projekte mit `*.tf`; ersetzt dort „je Modul bzw. Klasse eine eigene Datei“.

## Struktur
- Dateien: `terraform.tf` (`required_version`, `required_providers`), `providers.tf`, `main.tf` (wächst er: nach Bereich teilen, z. B. `network.tf`), `variables.tf`, `outputs.tf`, `locals.tf`. Lokale Module unter `modules/<name>/` mit derselben Aufteilung.
- Jede `variable` hat `type` und `description`, jeder `output` eine `description`. Secrets `sensitive = true` (stehen trotzdem im Klartext im State). Variable nur, wenn der Wert je Umgebung abweicht.
- `for_each` statt `count`, sobald Instanzen sich unterscheiden (stabile Adressen); `count` nur für an/aus.

## Versionen und Git
- Terraform, Provider und Registry-Module exakt pinnen: `.terraform.lock.hcl` kommt nicht ins Repo, der Pin ersetzt sie.
- `.gitignore`: `.terraform/`, `.terraform.lock.hcl`, `*.tfstate*`, Plan-Dateien, `*.tfvars` mit Secrets.
- Vor jedem Commit `terraform fmt -recursive` im Repo-Wurzelverzeichnis; der Schutz-Hook lehnt sonst ab.

## TDD
- Red/Green mit `terraform test` (`tests/*.tftest.hcl`). Jeder `run`-Block mit `command = plan` oder gegen `mock_provider`: Standard ist `apply` und legt echte Infrastruktur an.
- Prüfstufe am Ende statt Lint/Typecheck: `fmt -check -recursive`, `validate`, `tflint` (falls vorhanden), `terraform test`.
- Refactor: Ressourcen oder Module nur mit `moved {}`-Block umbenennen bzw. verschieben, sonst Destroy und Neuanlage.

## Plan, Apply, Abschluss
- Vor jedem Apply `terraform plan`. Jedes `destroy`/`replace` im Plan muss gewollt sein, sonst ist es ein Befund (bei Daten Critical). Kritische Ressourcen mit `lifecycle { prevent_destroy = true }`.
- `apply`, `destroy`, `import`, `state rm/mv` nur mit Freigabe des Nutzers, nie gegen Prod im Rahmen von Tests (der Schutz-Hook fragt nach).
- Frischer Clone: `terraform init -backend=false`, dann `validate` und `terraform test`.
- Security-Review: zusätzlich `trivy config .` oder `checkov -d .`, falls installiert.
