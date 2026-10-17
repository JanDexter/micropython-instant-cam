# Stage 3: the full flow once: capture, stretch, Floyd-Steinberg, print.
from array import array
import config, cam, dither
from printer import DP_EH600

W, H, N, S = config.FRAME_W, config.FRAME_H, config.FRAME_W * config.FRAME_H, config.ROW_BYTES
gray = bytearray(N)
bits = bytearray(S * H)
out = memoryview(bits)[config.X0:]
err = array("H", bytes(4 * (W + 2)))
hist = array("I", bytes(4 * 256))

cam.capture(gray)
dither.stretch(gray, N, hist, N * (config.STRETCH_PCT or 0) // 100)
dither.floyd_steinberg(gray, out, W, H, S, err)
p = DP_EH600()
p.init()
p.print_raster(bits, S, H)
p.feed(config.FEED_LINES)
