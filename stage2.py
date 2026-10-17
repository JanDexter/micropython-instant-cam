# Stage 2: one capture, printed twice (stacked): threshold, then Bayer.
import config, cam, dither
from printer import DP_EH600

W, H, N, S = config.FRAME_W, config.FRAME_H, config.FRAME_W * config.FRAME_H, config.ROW_BYTES
gray = bytearray(N)
bits = bytearray(S * H)
out = memoryview(bits)[config.X0:]
hist = __import__("array").array("I", bytes(4 * 256))

cam.capture(gray)
dither.stretch(gray, N, hist, N * (config.STRETCH_PCT or 0) // 100)
p = DP_EH600()
p.init()
p.print_text("threshold")
dither.threshold(gray, out, W, H, S, config.LEVEL)
p.print_raster(bits, S, H)
p.print_text("bayer")
dither.bayer(gray, out, W, H, S)
p.print_raster(bits, S, H)
p.feed(config.FEED_LINES)
