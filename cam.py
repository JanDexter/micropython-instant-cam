import sys
import config

try:
    from camera import Camera, PixelFormat, GrabMode
    c = Camera(pixel_format=PixelFormat.GRAYSCALE, frame_size=config.FRAME_SIZE,
               fb_count=2, grab_mode=GrabMode.LATEST, **config.CAM_PINS)
except Exception as e:
    print("ERROR: camera init failed:", repr(e))
    print("Check the camera firmware and board; set config.CAM_PINS if it has no defaults.")
    sys.exit()


def capture(buf):
    """Copy one GRAYSCALE frame into the preallocated buf. Stops if the size is wrong."""
    img = c.capture()
    if len(img) != len(buf):
        print("ERROR: frame is %d bytes, expected %d. Wrong firmware or pixel format "
              "(JPEG frame?)" % (len(img), len(buf)))
        sys.exit()
    buf[:] = img
    c.free_buffer()
