# Voron printer repo — working notes for Claude

- Printer: Klipper + Moonraker + Mainsail at http://192.168.3.50 (Moonraker API open to LAN, no auth needed).
  Useful endpoints: `/printer/objects/query?...`, `/server/files/...`, `/printer/gcode/script?script=...`,
  `/server/files/logs/klippy.log`, websocket at `/websocket` for live monitoring.
- `config/` mirrors `~/printer_data/config`. Always `python scripts/sync.py pull` and check `git status`
  before editing; commit printer-side changes separately from ours.
- Deploy only via `python scripts/deploy.py` (`--dry-run` first; `--yes` once the user approved).
- Never push config or send gcode that moves/heats the printer without the user's explicit go-ahead,
  and never while a print is running (check `print_stats.state` first). A RESTART during a print kills it.
- Don't edit below the `#*# SAVE_CONFIG` marker in printer.cfg — Klipper owns it.
- Known issues / cleanup ideas live in `docs/todo.md`; hardware inventory in `docs/hardware.md`.
