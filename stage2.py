# Stage 2: capture + threshold + print
import config, cam, dither, printer

bits = bytearray(config.STRIDE * config.FRAME_H)
view = memoryview(bits)[config.X0:]
img = cam.check()
dither.threshold(img, view, config.FRAME_W, config.FRAME_H, config.STRIDE, config.LEVEL)
printer.init()
printer.image(bits, config.STRIDE, config.FRAME_H)
printer.feed(config.FEED_LINES)
