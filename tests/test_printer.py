import pytest
import config
from printer import DP_EH600 as _DP


def DP_EH600():
    """Printer with the start-up wake byte already checked and cleared."""
    p = _DP()
    assert p.uart.sent == [bytes([0xFF])]
    p.uart.sent.clear()
    return p


def test_gs_v_0_header_known_values():
    p = DP_EH600()
    p.print_raster(bytes(48 * 24), 48, 24)
    hdr, data = p.uart.sent
    assert hdr == bytes([0x1D, 0x76, 0x30, 0x00, 48, 0, 24, 0])
    assert len(data) == 48 * 24


def test_bands_240_rows():
    p = DP_EH600()
    p.print_raster(bytes(48 * 240), 48, 240)
    sent = p.uart.sent
    assert len(sent) == 20                                   # 10 bands x (header, data)
    assert all(h == bytes([0x1D, 0x76, 0x30, 0x00, 48, 0, 24, 0]) for h in sent[0::2])
    assert sum(len(d) for d in sent[1::2]) == 48 * 240


def test_last_band_and_yh(monkeypatch):
    monkeypatch.setattr(config, "BAND_ROWS", 300)
    p = DP_EH600()
    p.print_raster(bytes(48 * 310), 48, 310)
    heights = [h[6] | h[7] << 8 for h in p.uart.sent[0::2]]
    assert heights == [300, 10]
    assert p.uart.sent[0][7] == 1 and p.uart.sent[0][6] == 44    # 300 = 0x012C


def test_raster_limits():
    p = DP_EH600()
    for w, h in ((49, 1), (0, 1), (48, 0), (48, 4096)):
        with pytest.raises(ValueError):
            p.print_raster(bytes(1), w, h)


def test_init_feed_text():
    p = DP_EH600()
    p.init()
    p.feed(4)
    p.self_test()
    assert p.uart.sent[0] == b"\x1b@"
    assert p.uart.sent[1] == bytes([0x1B, 0x37, config.HEAT_N1, config.HEAT_N2, config.HEAT_N3])
    assert p.uart.sent[2] == b"\x1bd\x04"
    assert p.uart.sent[3] == b"\x12T"


def test_status_none_without_rx(monkeypatch):
    monkeypatch.setattr(config, "RX_PIN", None)
    assert DP_EH600().status() is None


class ReplyUART:
    """Fake UART: answers GS r 1 with `paper`, ignores ESC v (like the real unit)."""
    def __init__(self, paper):
        self.paper, self.buf, self.sent = paper, b"", []

    def write(self, data):
        self.sent.append(bytes(data))
        if bytes(data) == b"\x1dr\x01":
            self.buf = bytes([self.paper])

    def any(self):
        return len(self.buf)

    def read(self):
        b, self.buf = self.buf, b""
        return b

    def readinto(self, rx):
        rx[0], self.buf = self.buf[0], self.buf[1:]
        return 1


def test_status_falls_back_to_gs_r():
    p = DP_EH600()
    p.uart = ReplyUART(0x60)                       # real reply seen on the unit: paper OK
    assert p.status(timeout_ms=20) == ""
    assert p.uart.sent == [b"\x1bv\x00", b"\x1dr\x01"]
    p.uart = ReplyUART(0x6C)                       # bits 2,3 set: out of paper
    assert p.status(timeout_ms=20) == "out of paper"
