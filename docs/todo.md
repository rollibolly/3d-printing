# Findings / TODO

Things noticed while importing the config on 2026-09-29. Nothing changed yet.

- **KAMP adaptive meshing is overridden.** `macros/printing.cfg` defines `[gcode_macro BED_MESH_CALIBRATE]`,
  included after KAMP, so it replaces KAMP's macro. Meshing still adapts because `PRINT_START` calls
  `BED_MESH_CALIBRATE ADAPTIVE=1` (Klipper's native adaptive mesh), so KAMP's meshing file is redundant.
- **Duplicate settings from printer.cfg vs the EBB sample file**: `[fan]`, `[heater_fan hotend_fan]`, and
  `[tmc2209 extruder]` are in both; the sample sets `stealthchop_threshold: 999999`, printer.cfg sets `0`
  (printer.cfg wins, being later). Worth folding into a single `toolhead.cfg`.
- **Unused files** (not included anywhere): `clean_nozzle.cfg`, `print_area_bed_mesh.cfg`,
  `KAMP/KAMP_Settings.cfg`, `timelapse.cfg` (also points at `/home/biqu/...`, wrong user).
- `[resonance_tester] probe_points: 100,100,20` — for a 350 bed, the center is 175,175.
- `PRINT_END` parks at X125 Y250 (250-size values); `PRINT_START` heats the bed twice and has no heat soak / chamber wait.
- Possible reorganization: split `printer.cfg` into `hardware/*.cfg` (steppers, toolhead, fans, lights) + `macros/*.cfg`.
