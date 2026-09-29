# Findings / TODO

## Done (2026-09-29 cleanup)
- Split printer.cfg into `hardware/*.cfg` and `macros/{printing,leveling,parking}.cfg`; dropped 250/300mm alternates.
- Folded the EBB sample file into `hardware/toolhead.cfg` (no more duplicated `[fan]`, `[heater_fan hotend_fan]`,
  `[tmc2209 extruder]`; effective values unchanged, extruder stays in spreadCycle).
- Removed KAMP adaptive meshing (was already overridden; native `ADAPTIVE=1` does it) and unused files:
  `clean_nozzle.cfg`, `print_area_bed_mesh.cfg`, `timelapse.cfg`, `KAMP/KAMP_Settings.cfg`, `KAMP/Adaptive_Meshing.cfg`.
- `resonance_tester` probe point -> bed center (175,175); `PRINT_END` parks at rear center of the 350 bed;
  `G32` uses axis limits; `PRINT_START` no longer re-waits for the bed.

## Open
- `PRINT_START`: add heat soak / chamber temperature wait, material-dependent behavior (pass MATERIAL/CHAMBER from Orca).
- `SMART_PARK` (KAMP) is included but unused; could park near the print while the nozzle heats in PRINT_START.
- `moonraker.conf`: `192.168.0.0/16` listed twice in `trusted_clients`.
- `fan_generic 4W_FAN0` on the EBB: confirm whether anything is connected, else remove.
- **Pi: set `allow-hotplug can0`** in /etc/network/interfaces.d/can0 (currently `auto can0`). The M8P is the
  USB-CAN bridge; any MCU reset (FIRMWARE_RESTART, or Klipper auto-reset on config CRC change after a deploy)
  re-enumerates USB and can0 stays DOWN until `sudo ip link set can0 up type can bitrate 1000000`.
