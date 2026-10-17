# micropython-instant-cam

Button -> grayscale photo -> contrast stretch -> 1-bit dither -> DP-EH600 thermal printer.
Three steps: capture (`cam.py`), dither (`dither.py`), print (`printer.py`).

## Wiring

Only these four connections are used.

| Signal | Board | Printer |
|---|---|---|
| UART1 TX | GPIO14 | RX |
| UART1 RX (optional) | GPIO47 | TX |
| Shutter | GPIO1 | other side of the button to GND (internal pull-up) |
| Ground | GND | GND (shared only GND; printer has its own 5 V supply) |

All pins live in `config.py`. Set `RX_PIN = None` if RX is not wired (no status checks then).
The board is a generic ESP32-S3 WROOM N16R8 CAM board, so **these pins are not verified against a pinout**. Camera pins are the ESP32-S3-EYE layout in `CAM_PINS` (verified: the camera returns 57600 bytes). They use GPIO4-13 and 15-18, so GPIO1, 14 and 47 do not clash.
The DP-EH600 manual rates the supply at 3.8 to 8.5 V.

## Setup

Firmware: cnadler86/micropython-camera-API, ESP32-S3 SPIRAM_OCT build (already flashed).

```
pip install mpremote pytest
python -m pytest tests                                   # host tests, CPython

mpremote cp config.py cam.py dither.py printer.py :      # modules
mpremote cp main.py stage1.py stage2.py stage3.py selftest.py bench.py :
```

## Run, in order

```
mpremote run selftest.py     # text + DC2 T at 9600, then 19200. Read the paper: the readable one wins
mpremote run stage1.py       # prints "printer OK", then the capture byte count (57600)
mpremote run stage2.py       # one capture printed twice: threshold, then Bayer
mpremote run stage3.py       # full flow with Floyd-Steinberg
mpremote run bench.py        # timings + memory, then press the shutter
mpremote cp main.py :main.py && mpremote reset     # runs on boot
```

If 19200 is the one that works, set `BAUD = 19200` in `config.py`.

## Tuning on the device

- `HEAT_N2` (default 80): higher = darker, slower, more current. If the board resets while printing, lower it and check the supply.
- `BAND_DELAY_MS` (default 0): at 9600 baud the UART is the bottleneck. Raise it only if the print garbles part-way down.
- `STRETCH_PCT` (default 1): % of pixels clipped at each end before stretching. `0` = plain min/max, `None` = off.
- `DITHER`: `fs`, `bayer`, `threshold` (+ `LEVEL`).
- `PAD`: `center` or `left`.

## Notes and known limitations

- A 240x240 image is 11.5 KB (about 12 s at 9600 baud). That is the UART, not the dither.
- `ESC v` is sent as `1B 76 00`; the manual's command takes an `n` parameter.
- `status()` checks paper, voltage over 9.5 V and head over 60 C; `main.py` skips printing and reports on the REPL when it flags a problem.
- The camera API has no capture-into-buffer call, so `cam.capture(buf)` copies the frame into a preallocated `bytearray`.
- Floyd-Steinberg stores its two error rows as unsigned 16 bit plus a bias, because viper `ptr16` reads are unsigned.
- Host tests run viper code as plain Python (a fake `micropython` module), so they check the logic, not viper compilation.
- `stage2` prints the two versions stacked, not side by side: two 240 px images do not fit in 384 dots.
- No Wi-Fi, Bluetooth, or JPEG on device.
