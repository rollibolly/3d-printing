# Voron 2.4 (350) — printer config & mods

Version-controlled configuration and notes for my custom Voron 2.4 (hostname `voron`, http://192.168.3.50/).

## Layout

```
config/          Mirror of ~/printer_data/config on the printer (the live Klipper/Moonraker config)
  printer.cfg      main Klipper config (+ SAVE_CONFIG block: PID, z_offset, input shaper, mesh)
  macros/          our own gcode macros
  KAMP/            Klipper Adaptive Meshing & Purging (copied files, not the symlinked upstream)
  led_effects/     Stealthburner LED effects
  moonraker.conf, crowsnest.conf, sonar.conf, KlipperScreen.conf
scripts/         Tooling that runs on this PC
  sync.py          pull/push printer config via Moonraker API
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
python scripts/sync.py push      # repo -> printer (changed files), then:
python scripts/sync.py restart   # RESTART klipper to load the config
python scripts/export_orca.py    # after changing profiles in Orca
```

SSH: `ssh voron` (key `~/.ssh/voron_ed25519`, alias in `~/.ssh/config`).

Rules of thumb:
- **Pull and commit before editing**, so changes made from Mainsail or by `SAVE_CONFIG` are captured separately from ours.
- After `SAVE_CONFIG` (PID tune, Z offset, shaper calibration) run a pull and commit with a message saying what was calibrated.
- Not tracked: read-only symlinks managed by Moonraker's update manager (`mainsail.cfg`, `KAMP/Configuration/`),
  and Klipper's dated `printer-YYYYMMDD_HHMMSS.cfg` backups — git history replaces those.
- `VORON_HOST` env var overrides the printer address.
