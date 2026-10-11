# All functions: src = 1 byte/pixel gray, out = packed 1 bpp (MSB first, 1 = black),
# stride = bytes per out row. Width must be a multiple of 8.
import micropython
from micropython import const

BIAS = const(1024)  # error buffer is unsigned uint16, so store error + BIAS
BAYER = bytes((8, 136, 40, 168, 200, 72, 232, 104,
               56, 184, 24, 152, 248, 120, 216, 88))  # 4x4 matrix * 16 + 8


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
    # err: array('H') of 2 * (w + 2): current row and next row, offset by 1 pixel
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


def floyd_steinberg_py(src, out, w, h, stride, err):
    """Same algorithm in plain Python. Only used by bench.py."""
    n = w + 2
    for i in range(2 * n):
        err[i] = BIAS
    for y in range(h):
        cur = (y & 1) * n
        nxt = ((y + 1) & 1) * n
        acc = 0
        for x in range(w):
            v = src[y * w + x] + err[cur + x + 1] - BIAS
            if v < 128:
                acc = (acc << 1) | 1
                e = v
            else:
                acc = acc << 1
                e = v - 255
            a = (e * 7) >> 4
            b = (e * 3) >> 4
            c = (e * 5) >> 4
            err[cur + x + 2] += a
            err[nxt + x] += b
            err[nxt + x + 1] += c
            err[nxt + x + 2] += e - a - b - c
            if (x & 7) == 7:
                out[y * stride + (x >> 3)] = acc
                acc = 0
        for i in range(n):
            err[cur + i] = BIAS


@micropython.viper
def upscale(src: ptr8, dst: ptr8, w: int, h: int, k: int):
    """Nearest-neighbour integer upscale into a preallocated (w*k * h*k) buffer."""
    ow = w * k
    for y in range(h * k):
        row = (y // k) * w
        for x in range(ow):
            dst[y * ow + x] = src[row + x // k]
