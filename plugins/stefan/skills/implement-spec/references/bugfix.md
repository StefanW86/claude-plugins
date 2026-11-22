# Bugfix

1. **Feedback-Schleife zuerst.** Ein Befehl (Test, curl, Playwright-Skript …), der genau das vom Nutzer beschriebene Symptom prüft, schnell und zuverlässig ist und jetzt rot wird. Einmal ausführen und die Ausgabe zeigen. Ohne diesen Befehl keine Hypothesen. Gelingt er nicht: sagen, was versucht wurde, und den Nutzer um Zugang zur Umgebung, Logs o. Ä. bitten.
2. **Minimieren:** das Szenario verkleinern, bis jedes verbleibende Element nötig ist.
3. **Hypothesen:** 3–5, nach Wahrscheinlichkeit geordnet, jede mit überprüfbarer Vorhersage („Ist X die Ursache, verschwindet der Fehler, wenn Y“). Dem Nutzer kurz zeigen, ohne darauf zu warten.
4. **Prüfen:** pro Probe nur eine Variable ändern. Debug-Logs mit eindeutigem Präfix, z. B. `[DEBUG-a4f2]`. Sackgasse: nach ~10 Proben ohne belegte Ursache nicht weiter probieren: belegte und widerlegte Hypothesen kurz zusammenfassen, dann mit frischem Kontext neu ansetzen (Subagent bzw. neue Session mit dieser Zusammenfassung) oder als `blocked` melden.
5. **Fix per TDD:** minimierte Reproduktion als Regressionstest an einem Seam, der das echte Fehlermuster trifft (Commit `test(fix): …`), dann Fix (Commit `fix: …`, Ursache in der Message). Gibt es keinen passenden Seam, das als Befund melden.
6. **Aufräumen:** ursprüngliche Schleife grün, Debug-Präfix per grep entfernt, Wegwerf-Code gelöscht.
