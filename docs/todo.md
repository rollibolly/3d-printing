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

## Done (2026-10-01 lights)
- STATUS_* macros only stop the toolhead's effects (a bare STOP_LED_EFFECTS used to kill the chamber strip too).
- Chamber strip follows printer status (led_effects/chamber_led_effects.cfg); caselight on during prints, off 10 min after.
- can-init.service on the Pi re-runs whenever can0 reappears (host/etc/systemd/system/can-init.service).
- PRINT_END parks 50mm above the bed (or 10mm above a taller print).

## Open
- Add a chamber thermistor: define `[temperature_sensor chamber]`, set `variable_chamber_sensor: 'chamber'` in
  `_PRINT_VARS`; `HEAT_SOAK CHAMBER=<C>` then waits for the chamber instead of the timer.
