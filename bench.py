# Part 1: time each step, ms (min / median / max over 10 runs after 2 warm-ups).
# Part 2: press the shutter once; time capture, dither and transmit separately.
import gc
from array import array
from machine import Pin
from time import ticks_ms, ticks_diff
import config, cam, dither
from printer import DP_EH600

W, H, N, S = config.FRAME_W, config.FRAME_H, config.FRAME_W * config.FRAME_H, config.ROW_BYTES
gray = bytearray(N)
bits = bytearray(S * H)
out = memoryview(bits)[config.X0:]
err = array("H", bytes(4 * (W + 2)))
hist = array("I", bytes(4 * 256))
clip = N * (config.STRETCH_PCT or 0) // 100
p = DP_EH600()
p.init()
gc.collect()
before = gc.mem_free()


def ms(f, *a):
    t = []
    for i in range(12):
        t0 = ticks_ms()
        f(*a)
        if i >= 2:
            t.append(ticks_diff(ticks_ms(), t0))
    t.sort()
    return t[0], t[5], t[9]


cam.capture(gray)
rows = (
    ("capture", cam.capture, (gray,)),
    ("stretch", dither.stretch, (gray, N, hist, clip)),
    ("threshold", dither.threshold, (gray, out, W, H, S, config.LEVEL)),
    ("threshold_py", dither.threshold_py, (gray, out, W, H, S, config.LEVEL)),
    ("bayer", dither.bayer, (gray, out, W, H, S)),
    ("bayer_py", dither.bayer_py, (gray, out, W, H, S)),
    ("floyd_steinberg (viper)", dither.floyd_steinberg, (gray, out, W, H, S, err)),
    ("floyd_steinberg_py", dither.floyd_steinberg_py, (gray, out, W, H, S, err)),
)
print("| step | min | median | max |")
print("|---|---:|---:|---:|")
for name, f, args in rows:
    print("| %s | %d | %d | %d |" % ((name,) + ms(f, *args)))
print("mem_free before:", before, "after:", gc.mem_free())

btn = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_UP)
print("press the shutter...")
while btn.value():
    pass
t0 = ticks_ms()
cam.capture(gray)
t1 = ticks_ms()
dither.stretch(gray, N, hist, clip)
dither.apply(gray, out, W, H, S, err)
t2 = ticks_ms()
p.print_raster(bits, S, H)                 # returns once the UART has drained
t3 = ticks_ms()
print("capture %d ms, stretch+dither %d ms, transmit %d ms, press to last byte sent %d ms"
      % (ticks_diff(t1, t0), ticks_diff(t2, t1), ticks_diff(t3, t2), ticks_diff(t3, t0)))
p.feed(config.FEED_LINES)
print("mem_free after shot:", gc.mem_free())
