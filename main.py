import gc
from array import array
from time import sleep_ms, ticks_ms, ticks_diff
from machine import Pin
import config, cam, dither
from printer import DP_EH600

W, H, N = config.FRAME_W, config.FRAME_H, config.FRAME_W * config.FRAME_H
btn = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(config.LED_PIN, Pin.OUT) if config.LED_PIN is not None else None
printer = DP_EH600()

# Preallocate everything once
gray = bytearray(N)                                       # captured frame
bits = bytearray(config.ROW_BYTES * H)                    # packed 1 bpp, margins stay 0
out = memoryview(bits)[config.X0:]                        # centered window, no copy
err = array("H", bytes(4 * (W + 2)))                      # two error rows
hist = array("I", bytes(4 * 256))                         # contrast histogram
clip = N * (config.STRETCH_PCT or 0) // 100


def shoot():
    problem = printer.status()                            # None = unknown, "" = OK
    if problem:
        print("printer:", problem)
        return
    cam.capture(gray)                                     # 1. capture
    if config.STRETCH_PCT is not None:
        dither.stretch(gray, N, hist, clip)
    dither.apply(gray, out, W, H, config.ROW_BYTES, err)  # 2. dither
    printer.print_raster(bits, config.ROW_BYTES, H)       # 3. print
    printer.feed(config.FEED_LINES)


printer.init()
gc.collect()
print("ready, free:", gc.mem_free())
shots = 0
while True:
    if btn.value() == 0:
        sleep_ms(config.DEBOUNCE_MS)
        if btn.value() == 0:
            led and led.on()
            t0 = ticks_ms()
            try:
                shoot()
                shots += 1
                print("shot %d: %d ms, free: %d" % (shots, ticks_diff(ticks_ms(), t0), gc.mem_free()))
            except Exception as e:
                print("shot failed:", repr(e))
            led and led.off()
            while btn.value() == 0:                       # ignore the press until released
                sleep_ms(10)
    sleep_ms(10)
