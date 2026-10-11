from array import array
import dither


def run(fn, pixels, w, h, *extra):
    stride = w // 8
    out = bytearray(stride * h)
    fn(bytes(pixels), out, w, h, stride, *extra)
    return out


def fs(pixels, w, h):
    return run(dither.floyd_steinberg, pixels, w, h, array("H", bytes(4 * (w + 2))))


def test_packing_8x2():
    # row 0: dark,light x4 -> 1010 1010 ; row 1: all dark -> 1111 1111
    px = [0, 255] * 4 + [0] * 8
    assert list(run(dither.threshold, px, 8, 2, 128)) == [0b10101010, 0xFF]


def test_packing_16x16_msb_first():
    px = [0 if x == 0 else 255 for y in range(16) for x in range(16)]
    out = run(dither.threshold, px, 16, 16, 128)
    assert len(out) == 32
    assert out[0::2] == bytes([0x80] * 16) and out[1::2] == bytes(16)
    diag = [0 if x == y else 255 for y in range(16) for x in range(16)]
    out = run(dither.threshold, diag, 16, 16, 128)
    for y in range(16):
        word = (out[2 * y] << 8) | out[2 * y + 1]
        assert word == 0x8000 >> y


def test_threshold_edges():
    px = [0, 127, 128, 255] * 2
    assert list(run(dither.threshold, px, 8, 1, 128)) == [0b11001100]  # <128 is black
    assert run(dither.threshold, px, 8, 1, 0)[0] == 0                  # nothing black
    assert run(dither.threshold, px, 8, 1, 255)[0] == 0b11101110       # all but 255
    assert run(dither.threshold, px, 8, 1, 127)[0] == 0b10001000       # only 0


def black_fraction(out):
    return sum(bin(b).count("1") for b in out) / (len(out) * 8)


def test_fs_flat_gray_half_black():
    out = fs([128] * (64 * 64), 64, 64)
    assert 0.45 < black_fraction(out) < 0.55


def test_fs_extremes():
    assert black_fraction(fs([0] * 256, 16, 16)) == 1
    assert black_fraction(fs([255] * 256, 16, 16)) == 0


def test_fs_py_matches_viper_version():
    import random
    random.seed(1)
    px = [random.randrange(256) for _ in range(32 * 32)]
    a = fs(px, 32, 32)
    b = run(dither.floyd_steinberg_py, px, 32, 32, array("H", bytes(4 * 34)))
    assert a == b


def test_bayer_flat_gray_half_black():
    out = run(dither.bayer, [128] * (64 * 64), 64, 64)
    assert 0.45 < black_fraction(out) < 0.55


def test_upscale():
    dst = bytearray(16)
    dither.upscale(bytes([1, 2, 3, 4]), dst, 2, 2, 2)
    assert list(dst) == [1, 1, 2, 2, 1, 1, 2, 2, 3, 3, 4, 4, 3, 3, 4, 4]
