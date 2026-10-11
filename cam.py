import sys
from camera import Camera, PixelFormat, GrabMode
import config

c = Camera(pixel_format=PixelFormat.GRAYSCALE, frame_size=config.FRAME_SIZE,
           fb_count=2, grab_mode=GrabMode.LATEST, **config.CAM_PINS)


def capture():
    """One grayscale frame, one byte per pixel (memoryview of the driver buffer)."""
    return c.capture()


def check():
    img = capture()
    if len(img) != config.FRAME_W * config.FRAME_H:
        print("ERROR: got %d bytes, expected %d. Wrong firmware or pixel format "
              "(JPEG frame?)" % (len(img), config.FRAME_W * config.FRAME_H))
        sys.exit()
    return img
