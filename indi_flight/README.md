# indi_flight: stage 2 of the INDI work (flight-ready INDI for PX4 quadcopters)

Workspace of the unattended orchestrator. Stage 1 is archived in `indi_project/` (read-only).

- `MISSION.md`: the orchestrator's prompt (owner file).
- `LESSONS.md`: rules learned in stage 1, read at every launch (owner file).
- `run_orchestrator.sh`, `guard.sh`, `claude_settings.json`, `watch.sh`: supervisor, command guard, session
  settings, log viewer. Same behaviour as in stage 1, with paths under `indi_flight/`, branch `feat/indi-flight`,
  and the archive protected from writes.
- `STATE.md`, `JOURNAL.md`, `DECISIONS.md`, `GATES.md`, `ANOMALIES.md`, `QUESTIONS.md`: written by the orchestrator
  (you write your answers in `QUESTIONS.md`).

## Start (owner, once)

```sh
cd <repo>
git tag indi-stage1-final 353c017971 && git push origin indi-stage1-final   # freeze stage 1
chmod -R a-w indi_project            # archive read-only on disk (undo: chmod -R u+w indi_project)
mkdir -p indi_flight/logs
nohup indi_flight/run_orchestrator.sh > indi_flight/logs/supervisor.nohup 2>&1 &
```

The supervisor creates and switches to `feat/indi-flight`; the orchestrator's first session commits this folder.
Stop with `touch indi_flight/STOP`. When the orchestrator needs you it writes to `indi_flight/QUESTIONS.md`; if it
is blocked it also creates `indi_flight/WAIT_OWNER` and the supervisor pauses: write your answer under the question
and remove that file. Follow progress in `indi_flight/STATE.md` or with `indi_flight/watch.sh`.
