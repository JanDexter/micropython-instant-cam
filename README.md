# micropython-instant-cam

Button -> grayscale photo -> 1-bit dither -> 58 mm thermal printer. Three steps: **capture** (`cam.py`), **dither** (`dither.py`), **print** (`printer.py`).

## Wiring (Freenove ESP32-S3 WROOM, N16R8 CAM -> DP-EH600)

| Signal | GPIO | Notes |
|---|---|---|
| UART1 TX -> printer RX | 14 | |
| UART1 RX <- printer TX | 21 | optional, status only (`PRINTER_RX = None` to disable) |
| Shutter button | 1 | other leg to GND, internal pull-up |
| LED | 2 | onboard ("LED ON" in Freenove pinout) |
| Printer GND | GND | common ground with the printer supply |
| Camera | 4-13, 15-18 | fixed by board, `config.CAM_PINS` |

Printer has its own supply. Checked against Freenove's ESP32S3_Pinout.png: no conflict with camera, PSRAM, SD, USB, UART0 or strapping pins.
The DP-EH600 manual rates the supply at 3.8 to 8.5 V; stay under that, not 9 V (status bit 3 flags > 9.5 V).

## Flashing

Firmware: [cnadler86/micropython-camera-API](https://github.com/cnadler86/micropython-camera-API), `SPIRAM_OCT` ESP32-S3 build. Already flashed, don't change.

## Commands

```
pip install mpremote pytest
python -m pytest tests                          # host tests (CPython)

mpremote cp config.py cam.py dither.py printer.py :   # upload modules
mpremote run stage1.py                          # capture only: 57600 bytes, pixel values
mpremote exec "import printer; printer.init(); printer.text('hello')"
mpremote run stage2.py                          # threshold print
mpremote run stage3.py                          # Floyd-Steinberg print
mpremote run bench.py                           # timing table
mpremote cp main.py :main.py                    # runs on boot
mpremote reset
```

If `hello` is garbled, set `BAUD` in `config.py`: default 19200, some units 9600.
Print the self-test page (shows the printer's own baud): `mpremote exec "import printer; printer.selftest()"`.
Status: `mpremote exec "import printer; print(repr(printer.status()))"` ('' = OK).

## Heat tuning

`HEAT_TIME` (default 80, x10 us): up for darker, slower prints; too low prints blank.
`HEAT_INTERVAL` (default 2): up for crisper, slower.
`HEAT_DOTS` (default 9 = 80 dots at once): up for faster, but draws more current. If the board resets mid-print, lower it and check the supply.

## Config

All in `config.py`: pins, `BAUD`, `HEAT_*`, `FRAME_SIZE`/`FRAME_W`/`FRAME_H`, `SCALE`, `PRINT_W`, `BAND_ROWS`, `BAND_MS`, `DITHER` (`fs`, `bayer`, `threshold`).
Image is centered in `PRINT_W`; image width must be a multiple of 8 and `PRINT_W - width` a multiple of 16.

## Notes

- Bit format: MSB first, 1 = black, row stride = width / 8.
- `floyd_steinberg` is viper; `floyd_steinberg_py` exists only for `bench.py`.
- If the board resets while printing, it's power (supply or ground), not code.
