# Findings / TODO

## Done (2026-09-29 cleanup)
- Split printer.cfg into `hardware/*.cfg` and `macros/{printing,leveling,parking}.cfg`; dropped 250/300mm alternates.
- Folded the EBB sample file into `hardware/toolhead.cfg` (no more duplicated `[fan]`, `[heater_fan hotend_fan]`,
  `[tmc2209 extruder]`; effective values unchanged, extruder stays in spreadCycle).
- Removed KAMP adaptive meshing (was already overridden; native `ADAPTIVE=1` does it) and unused files:
  `clean_nozzle.cfg`, `print_area_bed_mesh.cfg`, `timelapse.cfg`, `KAMP/KAMP_Settings.cfg`, `KAMP/Adaptive_Meshing.cfg`.
- `resonance_tester` probe point -> bed center (175,175); `PRINT_END` parks at rear center of the 350 bed;
  `G32` uses axis limits; `PRINT_START` no longer re-waits for the bed.

## Done (2026-09-29 PRINT_START)
- Material-aware PRINT_START (soak, chamber fans, Smart Park), fans off on PRINT_END/cancel; Orca passes MATERIAL/CHAMBER.
- Heat soak is manual (`HEAT_SOAK` / `CANCEL_HEAT_SOAK`, non-blocking); PRINT_START never soaks.
- `M106` ignores slicer fan indexes (Orca's `M106 P3` used to drive the part fan).

## Done (2026-10-01)
- Removed unused `fan_generic 4W_FAN0` (0 RPM on its tachometer) and the duplicate Moonraker trusted client.

## Open
- Install `host/etc/systemd/system/can-init.service` on the Pi so can0 comes back after M8P resets
  (`allow-hotplug` had no effect: ifupdown isn't installed, can0 is brought up by can-init.service at boot only).
- Add a chamber thermistor: define `[temperature_sensor chamber]`, set `variable_chamber_sensor: 'chamber'` in
  `_PRINT_VARS`; `HEAT_SOAK CHAMBER=<C>` then waits for the chamber instead of the timer.
