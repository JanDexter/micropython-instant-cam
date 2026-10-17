# DP-EH600, ESC/POS-style. No flow control: the UART baud rate paces the writes.
from machine import UART
from time import sleep_ms, ticks_ms, ticks_diff
import config


class DP_EH600:
    def __init__(self, baud=config.BAUD):
        pins = {"tx": config.TX_PIN}
        if config.RX_PIN is not None:
            pins["rx"] = config.RX_PIN
        self.uart = UART(config.UART_ID, baudrate=baud, **pins)
        sleep_ms(50)
        self.uart.write(b"\xff")      # opening the pins glitches TX; let this byte absorb it
        sleep_ms(50)
        self.hdr = bytearray(b"\x1d\x76\x30\x00\0\0\0\0")   # GS v 0 m xL xH yL yH, reused
        self.rx = bytearray(1)

    def init(self):
        self.uart.write(b"\x1b@")                           # ESC @ (resets heat, so set after)
        sleep_ms(50)
        self.uart.write(bytes((0x1B, 0x37, config.HEAT_N1, config.HEAT_N2, config.HEAT_N3)))

    def self_test(self):
        self.uart.write(b"\x12T")                           # DC2 T

    def print_text(self, s):
        self.uart.write(s + "\n")

    def print_raster(self, buf, w_bytes, h):
        """GS v 0 in bands of BAND_ROWS rows, one command each. 1 = black, MSB first."""
        if not 1 <= w_bytes <= 48 or not 1 <= h <= 4095:
            raise ValueError("raster must be 1-48 bytes wide, 1-4095 rows")
        mv, hdr = memoryview(buf), self.hdr
        for y in range(0, h, config.BAND_ROWS):
            rows = min(config.BAND_ROWS, h - y)
            hdr[4], hdr[5], hdr[6], hdr[7] = w_bytes & 255, w_bytes >> 8, rows & 255, rows >> 8
            self.uart.write(hdr)
            self.uart.write(mv[y * w_bytes:(y + rows) * w_bytes])
            if config.BAND_DELAY_MS:
                sleep_ms(config.BAND_DELAY_MS)
        self.uart.flush()                                   # wait until the last byte is sent

    def feed(self, n):
        self.uart.flush()
        self.uart.write(b"\x1bd" + bytes((n,)))             # ESC d n

    def _ask(self, cmd, timeout_ms):
        """Send cmd, return the 1-byte reply or None after timeout_ms."""
        while self.uart.any():
            self.uart.read()
        self.uart.write(cmd)
        t0 = ticks_ms()
        while not self.uart.any():
            if ticks_diff(ticks_ms(), t0) > timeout_ms:
                return None
            sleep_ms(5)
        self.uart.readinto(self.rx)
        return self.rx[0]

    def status(self, timeout_ms=300):
        """'' = OK, else the problems as text. None if RX is not wired or no reply."""
        if config.RX_PIN is None:
            return None
        s = self._ask(b"\x1bv\x00", timeout_ms)             # ESC v 0: paper, voltage, heat
        if s is not None:
            return ("out of paper " if s & 4 else "") + ("voltage >9.5V " if s & 8 else "") \
                + ("head >60C" if s & 64 else "")
        s = self._ask(b"\x1dr\x01", timeout_ms)             # GS r 1: paper sensor only
        if s is None:
            return None
        return "out of paper" if s & 0x0C else ""           # some units ignore ESC v
