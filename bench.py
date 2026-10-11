# Time each step on the device: ms, min / median / max over 10 runs after 2 warm-ups
from array import array
from time import ticks_ms, ticks_diff
import config, cam, dither, printer

W, H, ST = config.FRAME_W, config.FRAME_H, config.STRIDE
bits = bytearray(ST * H)
view = memoryview(bits)[config.X0:]
err = array("H", bytes(4 * (W + 2)))
img = cam.check()
printer.init()


def ms(f, *a):
    t = []
    for i in range(12):
        t0 = ticks_ms()
        f(*a)
        if i >= 2:
            t.append(ticks_diff(ticks_ms(), t0))
    t.sort()
    return t[0], t[5], t[9]


rows = (
    ("capture", cam.capture, ()),
    ("threshold", dither.threshold, (img, view, W, H, ST, config.LEVEL)),
    ("bayer", dither.bayer, (img, view, W, H, ST)),
    ("floyd_steinberg_py", dither.floyd_steinberg_py, (img, view, W, H, ST, err)),
    ("floyd_steinberg (viper)", dither.floyd_steinberg, (img, view, W, H, ST, err)),
    ("print", printer.image, (bits, ST, H)),
)
print("| step | min | median | max |")
print("|---|---:|---:|---:|")
for name, f, args in rows:
    print("| %s | %d | %d | %d |" % ((name,) + ms(f, *args)))
