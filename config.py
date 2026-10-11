from camera import FrameSize

# Pins (Freenove ESP32-S3 WROOM; camera pins are fixed by the board)
BUTTON_PIN = 1       # to GND, internal pull-up
LED_PIN = 2          # onboard LED
PRINTER_TX = 14      # UART1 TX -> printer RX. GPIO43/44 stay free for the REPL
PRINTER_RX = 21      # UART1 RX <- printer TX (status only). None if not wired
UART_ID = 1
BAUD = 19200         # DP-EH600 default; some units ship at 9600

# Heat, ESC 7 n1 n2 n3 (manual defaults). Longer time = darker but slower
HEAT_DOTS = 9        # max dots heated at once, units of 8 (+1). More = faster, more current
HEAT_TIME = 80       # units of 10 us
HEAT_INTERVAL = 2    # units of 10 us

CAM_PINS = dict(
    data_pins=[11, 9, 8, 10, 12, 18, 17, 16],
    vsync_pin=6, href_pin=7, pclk_pin=13, xclk_pin=15,
    sda_pin=4, scl_pin=5, xclk_freq=20_000_000,
)

# Frame (FRAME_W/H must match FRAME_SIZE)
FRAME_SIZE = FrameSize.R240X240
FRAME_W, FRAME_H = 240, 240
SCALE = 1            # integer nearest-neighbour upscale

# Print
PRINT_W = 384        # dots per line
BAND_ROWS = 24       # rows per GS v 0 chunk
BAND_MS = 60         # pause between bands
FEED_LINES = 4

# Dither: "fs" | "bayer" | "threshold"
DITHER = "fs"
LEVEL = 128          # threshold cutoff

# Derived
IMG_W, IMG_H = FRAME_W * SCALE, FRAME_H * SCALE
STRIDE = PRINT_W // 8
X0 = (PRINT_W - IMG_W) // 16     # centering offset, in bytes
assert IMG_W <= PRINT_W <= 384 and IMG_W % 8 == 0 and (PRINT_W - IMG_W) % 16 == 0, "image must be byte-aligned"
