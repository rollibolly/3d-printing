# Voron 2.4 (350) — printer config & mods

Version-controlled configuration and notes for my custom Voron 2.4 (hostname `voron`, http://192.168.3.50/).

## Layout

```
config/          Mirror of ~/printer_data/config on the printer (the live Klipper/Moonraker config)
  printer.cfg      includes + general limits (+ SAVE_CONFIG block: PID, z_offset, input shaper, mesh)
  hardware/        mcu, steppers, toolhead (extruder/probe/adxl), bed (heater/QGL/mesh), fans, lights
  macros/          our gcode macros: printing (PRINT_START/END), leveling, parking; all auto-included
  KAMP/            KAMP line purge + smart park (copied files, not the symlinked upstream)
  led_effects/     Stealthburner LED effects + STATUS_* macros
  moonraker.conf, crowsnest.conf, sonar.conf, KlipperScreen.conf
scripts/         Tooling that runs on this PC
  sync.py          pull printer config into the repo / show differences (Moonraker API)
  deploy.py        deploy config/ to the printer with safety checks, restarts and auto-rollback
  export_orca.py   copy OrcaSlicer Voron profiles into slicer/orca/
docs/            Hardware notes, wiring, decisions, TODOs
calibration/     (when needed) input shaper graphs, PA/flow tests, PID results, with dates
slicer/orca/     OrcaSlicer user profiles (machine / filament / process), exported from %APPDATA%
prints/          (when needed) notes & analysis from monitored prints
```

## Workflow

```bash
python scripts/sync.py pull      # printer -> repo, then review `git diff` and commit
python scripts/sync.py status    # what differs between printer and repo
python scripts/deploy.py --dry-run   # preview a deploy of the committed config
python scripts/deploy.py             # repo -> printer, restart affected services, roll back on failure
python scripts/deploy.py --status    # which commit is on the printer
python scripts/export_orca.py    # after changing profiles in Orca
```

SSH: `ssh voron` (key `~/.ssh/voron_ed25519`, alias in `~/.ssh/config`).

Deploy safety (`deploy.py`):
- refuses while printing/paused; deploys only committed config (`--allow-dirty` to test uncommitted edits)
- refuses if a printer file was edited but never pulled (`sync.py pull` + commit first, or `--force`)
- restarts only what changed: Klipper for `.cfg`, the matching service for moonraker/crowsnest/KlipperScreen/sonar conf
- if Klipper comes back in error, restores the previous files and restarts again
- `--delete` removes printer files that were deleted in the repo (off by default)

Rules of thumb:
- **Pull and commit before editing**, so changes made from Mainsail or by `SAVE_CONFIG` are captured separately from ours.
- After `SAVE_CONFIG` (PID tune, Z offset, shaper calibration) run a pull and commit with a message saying what was calibrated.
- Not tracked: read-only symlinks managed by Moonraker's update manager (`mainsail.cfg`, `KAMP/Configuration/`),
  and Klipper's dated `printer-YYYYMMDD_HHMMSS.cfg` backups — git history replaces those.
- `VORON_HOST` env var overrides the printer address.
