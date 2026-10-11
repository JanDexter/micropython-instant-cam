import gc
from array import array
from time import sleep_ms
from machine import Pin
import config, cam, dither, printer

W, H, S = config.FRAME_W, config.FRAME_H, config.SCALE
btn = Pin(config.BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(config.LED_PIN, Pin.OUT)

# Preallocate everything once
bits = bytearray(config.STRIDE * config.IMG_H)           # packed 1 bpp, margins stay 0
view = memoryview(bits)[config.X0:]                      # centered window, no copy
big = bytearray(config.IMG_W * config.IMG_H) if S > 1 else None
err = array("H", bytes(4 * (config.IMG_W + 2)))


def shoot():
    problem = printer.status()                           # None = unknown, "" = OK
    if problem:
        print("printer:", problem)
        return
    img = cam.capture()                                  # capture
    if big:
        dither.upscale(img, big, W, H, S)
        img = big
    w, h, st = config.IMG_W, config.IMG_H, config.STRIDE
    if config.DITHER == "fs":                            # dither
        dither.floyd_steinberg(img, view, w, h, st, err)
    elif config.DITHER == "bayer":
        dither.bayer(img, view, w, h, st)
    else:
        dither.threshold(img, view, w, h, st, config.LEVEL)
    printer.image(bits, config.STRIDE, config.IMG_H)     # print
    printer.feed(config.FEED_LINES)


cam.check()
printer.init()
gc.collect()
print("ready, free:", gc.mem_free())
while True:
    if btn.value() == 0:
        sleep_ms(50)
        if btn.value() == 0:
            led.on()
            try:
                shoot()
            except Exception as e:
                print("shot failed:", repr(e))
            led.off()
            gc.collect()
            print("free:", gc.mem_free())
            while btn.value() == 0:
                sleep_ms(10)
    sleep_ms(10)
