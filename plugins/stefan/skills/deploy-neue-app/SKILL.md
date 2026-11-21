---
name: deploy-neue-app
description: Konventionen für Entwicklung und Deployment neuer Apps auf dem Homelab (~/dev, Prod-Checkout, swdhomelab/deploy, Docker Compose, cloudflared). Verwenden, wenn eine neue App entwickelt, angelegt, für Prod eingerichtet oder deployt werden soll.
---

# Deployment neuer Apps
- Entwicklung in `~/dev/<App>`, Repo privat unter `StefanW86/<app>`.
- Prod-Checkout `/home/stefan/<app>`. Dort nie direkt ändern, er wird nur vom Deploy aktualisiert.
- Ablauf: Merge nach `main` → CI im App-Repo → `repository_dispatch` an `swdhomelab/deploy` (der Org-Runner bedient keine persönlichen Repos) → Deploy läuft auf diesem Host.
- Neue App eintragen: Eintrag `deploy_<app>` in `swdhomelab/deploy` anlegen. Änderungen dort per `gh api` (contents PUT), nicht über den lokalen Clone.
- Laufende Deploys beobachten: `gh run list -R swdhomelab/deploy`. Nur notfalls manuell auslösen: `gh workflow run deploy.yml -R swdhomelab/deploy -f repo=StefanW86/<app> -f sha=<sha>`.
- Docker Compose: öffentlich erreichbare Apps als `app` + `cloudflared` ohne Host-Port, `TUNNEL_TOKEN` kommt in die Prod-`.env`. Reine LAN-Apps bekommen einen festen Port (z. B. 8095).
- Secrets nur in `/home/stefan/<app>/.env` (chmod 600), nie im Repo.
- Secret `DEPLOY_DISPATCH_TOKEN` im App Repo vom Nutzer eintragen lassen
- Healthcheck `/api/health` einbauen. Datenbanken in `~/backup.sh` aufnehmen (Snapshot vor dem Backup).
- E2E-Tests nie gegen Prod, sondern gegen eine lokale Instanz auf einem eigenen Port. Lokale Server per PID auf dem Port beenden, nie per `pkill -f` (das trifft Prod).
