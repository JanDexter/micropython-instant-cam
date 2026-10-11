# DP-EH600 (ESC/POS-style). Commands per the DP-EH600 technical manual.
from machine import UART
from time import sleep_ms
import config

uart = UART(config.UART_ID, baudrate=config.BAUD, tx=config.PRINTER_TX,
            rx=config.PRINTER_RX)
hdr = bytearray(b"\x1d\x76\x30\x00\0\0\0\0")  # GS v 0 m xL xH yL yH, reused
reply = bytearray(1)


def heat():
    uart.write(bytes((0x1B, 0x37, config.HEAT_DOTS, config.HEAT_TIME, config.HEAT_INTERVAL)))


def init():
    uart.write(b"\x1b@")                  # ESC @ resets heat settings, so set them after
    sleep_ms(50)
    heat()


def text(s):
    uart.write(s + "\n")


def image(bits, width_bytes, height):
    """GS v 0 raster, one command per band so the printer buffer never overflows."""
    mv = memoryview(bits)
    for y in range(0, height, config.BAND_ROWS):
        rows = min(config.BAND_ROWS, height - y)
        hdr[4], hdr[5], hdr[6], hdr[7] = width_bytes & 255, width_bytes >> 8, rows & 255, rows >> 8
        uart.write(hdr)
        uart.write(mv[y * width_bytes:(y + rows) * width_bytes])
        sleep_ms(config.BAND_MS)


def feed(n):
    uart.write(b"\x1bd" + bytes((n,)))    # ESC d n: print buffer and feed n lines


def status():
    """ESC v 0 -> '' if OK, else problems as text. None if RX is not wired or no reply."""
    if config.PRINTER_RX is None:
        return None
    while uart.any():
        uart.read()
    uart.write(b"\x1bv\x00")
    sleep_ms(100)
    if uart.readinto(reply) != 1:
        return None
    s = reply[0]
    return ("out of paper " if s & 4 else "") + ("voltage >9.5V " if s & 8 else "") \
        + ("head >60C" if s & 64 else "")


def selftest():
    uart.write(b"\x12T")                  # DC2 T
