# Stage 1: capture only. Prove the camera gives raw grayscale.
import cam
img = cam.check()
print("bytes:", len(img))
print("first 16:", list(img[:16]))
print("JPEG header!" if img[0] == 0xFF and img[1] == 0xD8 else "looks like pixels")
