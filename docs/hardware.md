# Hardware

Derived from the config on 2026-09-29; items marked **(?)** are guesses to confirm.

| Part | Details |
|---|---|
| Frame | Voron 2.4, 350×350 build, Z max 340 |
| Host | Raspberry Pi CM4, Debian 13 (trixie), user `rollibolly` |
| Mainboard | BTT Manta M8P v2 (STM32H723, CM4 on board), running as USB-CAN bridge (`can0`, 1 Mbit, gs_usb), uuid `5d91cd650d3f` |
| Toolhead board | BTT EBB SB2209 (RP2040) over CAN, uuid `a03500b699cc` |
| Toolhead | Stealthburner **(?)**, extruder gear ratio 50:10 (Clockwork 2 **(?)**) |
| Hotend | Phaetus Dragon HF **(?)**, PT100 via MAX31865 (2-wire), max 280 °C |
| Probe | Nozzle probe on EBB gpio22 (Voron Tap **(?)**), probing at ≤150 °C |
| Endstops | X on toolhead (EBB gpio24), Y on PF3, Z = probe |
| Motors | X/Y TMC2209 0.9 A, 4× Z TMC2209 0.8 A, 1.8° steppers, 16 microsteps |
| Bed | Generic 3950 thermistor, max 115 °C |
| Accelerometer | ADXL345 on the EBB |
| Fans | Part (EBB gpio13), hotend (EBB gpio14), Nevermore (PF8), exhaust (PF7), 2× electronics bay (PF9, PF6) |
| Lights | Caselight PWM (PA3), 36-LED neopixel "disco_stick" (PD15), Stealthburner LEDs |
| Extras | KlipperScreen, Crowsnest camera, Sonar (wifi keepalive), Moonraker timelapse **(?)** |

## Current tuning (from SAVE_CONFIG)

- Input shaper: X `3hump_ei` @ 100.6 Hz, Y `mzv` @ 39.0 Hz
- Pressure advance 0.04, firmware retraction 0.3 mm @ 40 mm/s
- Limits: 300 mm/s, 3000 mm/s², SCV 5
