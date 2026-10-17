# Stage 1: wiring + camera. Text first, then capture and report the byte count.
import config, cam
from printer import DP_EH600

p = DP_EH600()
p.init()
p.print_text("stage1: printer OK")
gray = bytearray(config.FRAME_W * config.FRAME_H)
cam.capture(gray)
msg = "%d bytes, first: %s" % (len(gray), list(gray[:8]))
print(msg)
p.print_text(msg)
p.feed(config.FEED_LINES)
