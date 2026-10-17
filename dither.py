# src: 1 byte/pixel gray. out: packed 1 bpp, MSB first, 1 = black, `stride` bytes per row.
# w must be a multiple of 8. Each viper function has a plain-Python twin (_py) for a PC.
import micropython
from micropython import const
import config

BIAS = const(1024)  # error rows are unsigned 16 bit, so store error + BIAS
BAYER = bytes((8, 136, 40, 168, 200, 72, 232, 104,
               56, 184, 24, 152, 248, 120, 216, 88))  # 4x4 matrix * 16 + 8


@micropython.viper
def stretch(buf: ptr8, n: int, hist: ptr32, clip: int):
    """Contrast stretch in place. clip = pixels ignored at each end of the histogram."""
    for i in range(256):
        hist[i] = 0
    for i in range(n):
        hist[buf[i]] = int(hist[buf[i]]) + 1
    lo = 0
    acc = int(hist[0])
    while acc <= clip and lo < 255:
        lo += 1
        acc += int(hist[lo])
    hi = 255
    acc = int(hist[255])
    while acc <= clip and hi > 0:
        hi -= 1
        acc += int(hist[hi])
    span = hi - lo
    if span < 16:
        return
    k = (255 << 8) // span
    for i in range(n):
        v = ((int(buf[i]) - lo) * k) >> 8
        if v < 0:
            v = 0
        if v > 255:
            v = 255
        buf[i] = v


@micropython.viper
def threshold(src: ptr8, out: ptr8, w: int, h: int, stride: int, level: int):
    for y in range(h):
        acc = 0
        for x in range(w):
            acc = (acc << 1) | (1 if int(src[y * w + x]) < level else 0)
            if (x & 7) == 7:
                out[y * stride + (x >> 3)] = acc
                acc = 0


@micropython.viper
def bayer(src: ptr8, out: ptr8, w: int, h: int, stride: int):
    m = ptr8(BAYER)
    for y in range(h):
        acc = 0
        for x in range(w):
            t = int(m[((y & 3) << 2) | (x & 3)])
            acc = (acc << 1) | (1 if int(src[y * w + x]) < t else 0)
            if (x & 7) == 7:
                out[y * stride + (x >> 3)] = acc
                acc = 0


@micropython.viper
def floyd_steinberg(src: ptr8, out: ptr8, w: int, h: int, stride: int, err: ptr16):
    # err: array('H') of 2 * (w + 2): this row and the next, shifted by one pixel
    n = w + 2
    for i in range(2 * n):
        err[i] = BIAS
    for y in range(h):
        cur = (y & 1) * n
        nxt = ((y + 1) & 1) * n
        acc = 0
        for x in range(w):
            v = int(src[y * w + x]) + int(err[cur + x + 1]) - BIAS
            if v < 128:
                acc = (acc << 1) | 1
                e = v
            else:
                acc = acc << 1
                e = v - 255
            a = (e * 7) >> 4
            b = (e * 3) >> 4
            c = (e * 5) >> 4
            err[cur + x + 2] = int(err[cur + x + 2]) + a
            err[nxt + x] = int(err[nxt + x]) + b
            err[nxt + x + 1] = int(err[nxt + x + 1]) + c
            err[nxt + x + 2] = int(err[nxt + x + 2]) + e - a - b - c
            if (x & 7) == 7:
                out[y * stride + (x >> 3)] = acc
                acc = 0
        for i in range(n):
            err[cur + i] = BIAS


def apply(src, out, w, h, stride, err):
    """Dither with the mode in config.DITHER."""
    if config.DITHER == "fs":
        floyd_steinberg(src, out, w, h, stride, err)
    elif config.DITHER == "bayer":
        bayer(src, out, w, h, stride)
    else:
        threshold(src, out, w, h, stride, config.LEVEL)


# ---- Pure-Python references (PC tests, and the "before" in bench.py) ----

def stretch_py(buf, n, hist, clip):
    for i in range(256):
        hist[i] = 0
    for i in range(n):
        hist[buf[i]] += 1
    lo, acc = 0, hist[0]
    while acc <= clip and lo < 255:
        lo += 1
        acc += hist[lo]
    hi, acc = 255, hist[255]
    while acc <= clip and hi > 0:
        hi -= 1
        acc += hist[hi]
    if hi - lo < 16:
        return
    k = (255 << 8) // (hi - lo)
    for i in range(n):
        buf[i] = min(255, max(0, ((buf[i] - lo) * k) >> 8))


def _pack_py(src, out, w, h, stride, is_black):
    for y in range(h):
        acc = 0
        for x in range(w):
            acc = (acc << 1) | (1 if is_black(x, y, src[y * w + x]) else 0)
            if x & 7 == 7:
                out[y * stride + (x >> 3)] = acc
                acc = 0


def threshold_py(src, out, w, h, stride, level):
    _pack_py(src, out, w, h, stride, lambda x, y, v: v < level)


def bayer_py(src, out, w, h, stride):
    _pack_py(src, out, w, h, stride, lambda x, y, v: v < BAYER[((y & 3) << 2) | (x & 3)])


def floyd_steinberg_py(src, out, w, h, stride, err):
    n = w + 2
    for i in range(2 * n):
        err[i] = BIAS
    for y in range(h):
        cur, nxt = (y & 1) * n, ((y + 1) & 1) * n
        acc = 0
        for x in range(w):
            v = src[y * w + x] + err[cur + x + 1] - BIAS
            if v < 128:
                acc, e = (acc << 1) | 1, v
            else:
                acc, e = acc << 1, v - 255
            a, b, c = (e * 7) >> 4, (e * 3) >> 4, (e * 5) >> 4
            err[cur + x + 2] += a
            err[nxt + x] += b
            err[nxt + x + 1] += c
            err[nxt + x + 2] += e - a - b - c
            if x & 7 == 7:
                out[y * stride + (x >> 3)] = acc
                acc = 0
        for i in range(n):
            err[cur + i] = BIAS
