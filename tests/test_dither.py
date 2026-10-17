import random
from array import array
import config, dither


def run(fn, pixels, w, h, *extra):
    stride = w // 8
    out = bytearray(stride * h)
    fn(bytes(pixels), out, w, h, stride, *extra)
    return out


def fs(fn, pixels, w, h):
    return run(fn, pixels, w, h, array("H", bytes(4 * (w + 2))))


def black(out):
    return sum(bin(b).count("1") for b in out) / (len(out) * 8)


def test_packing_8x2():
    px = [0, 255] * 4 + [0] * 8            # row 0: 1010 1010, row 1: all black
    assert list(run(dither.threshold, px, 8, 2, 128)) == [0b10101010, 0xFF]


def test_packing_16x16_msb_first():
    diag = [0 if x == y else 255 for y in range(16) for x in range(16)]
    out = run(dither.threshold, diag, 16, 16, 128)
    for y in range(16):
        assert (out[2 * y] << 8) | out[2 * y + 1] == 0x8000 >> y


def test_threshold_edges():
    px = [0, 127, 128, 255] * 2
    assert run(dither.threshold, px, 8, 1, 128)[0] == 0b11001100   # < level is black
    assert run(dither.threshold, px, 8, 1, 0)[0] == 0
    assert run(dither.threshold, px, 8, 1, 255)[0] == 0b11101110
    assert run(dither.threshold, px, 8, 1, 127)[0] == 0b10001000


def test_row_padding_center_and_left(monkeypatch):
    """Image is written through a window into the 48-byte row; margins stay zero."""
    for pad, x0 in (("center", 9), ("left", 0)):
        monkeypatch.setattr(config, "PAD", pad)
        x0_calc = (config.ROW_BYTES - config.FRAME_W // 8) // 2 if pad == "center" else 0
        assert x0_calc == x0
        bits = bytearray(48 * 2)
        out = memoryview(bits)[x0:]
        dither.threshold(bytes([0] * 240 * 2), out, 240, 2, 48, 128)   # all black
        for row in (bits[:48], bits[48:]):
            assert row[:x0] == bytes(x0)
            assert row[x0:x0 + 30] == b"\xff" * 30
            assert row[x0 + 30:] == bytes(48 - x0 - 30)
    assert config.X0 == 9                                              # default is centered


def test_fs_flat_gray_half_black():
    assert 0.45 < black(fs(dither.floyd_steinberg, [128] * 4096, 64, 64)) < 0.55


def test_fs_extremes():
    assert black(fs(dither.floyd_steinberg, [0] * 256, 16, 16)) == 1
    assert black(fs(dither.floyd_steinberg, [255] * 256, 16, 16)) == 0


def test_bayer_flat_gray_half_black():
    assert 0.45 < black(run(dither.bayer, [128] * 4096, 64, 64)) < 0.55


def test_references_match():
    random.seed(1)
    px = [random.randrange(256) for _ in range(32 * 32)]
    assert fs(dither.floyd_steinberg, px, 32, 32) == fs(dither.floyd_steinberg_py, px, 32, 32)
    assert run(dither.bayer, px, 32, 32) == run(dither.bayer_py, px, 32, 32)
    assert run(dither.threshold, px, 32, 32, 100) == run(dither.threshold_py, px, 32, 32, 100)


def test_stretch():
    px = bytearray([60 + (i % 100) for i in range(1000)])      # range 60..159
    ref = bytearray(px)
    dither.stretch(px, 1000, array("I", bytes(1024)), 0)
    dither.stretch_py(ref, 1000, array("I", bytes(1024)), 0)
    assert px == ref and min(px) == 0 and max(px) >= 250
    flat = bytearray([100] * 100)                              # no range: left alone
    dither.stretch(flat, 100, array("I", bytes(1024)), 0)
    assert flat == bytearray([100] * 100)
