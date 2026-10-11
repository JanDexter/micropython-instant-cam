# Stage 3: full pipeline, Floyd-Steinberg
from array import array
import config, cam, dither, printer

bits = bytearray(config.STRIDE * config.FRAME_H)
view = memoryview(bits)[config.X0:]
err = array("H", bytes(4 * (config.FRAME_W + 2)))
img = cam.check()
dither.floyd_steinberg(img, view, config.FRAME_W, config.FRAME_H, config.STRIDE, err)
printer.init()
printer.image(bits, config.STRIDE, config.FRAME_H)
printer.feed(config.FEED_LINES)
