from camera import FrameSize

# Pins. None of these are verified against your board's pinout; see README.
BUTTON_PIN = 1       # to GND, internal pull-up
LED_PIN = None       # status LED pin, None = no LED (onboard LED pin not verified)
UART_ID = 1
TX_PIN = 14          # ESP32 TX -> printer RX
RX_PIN = 47          # printer TX -> ESP32 RX. Optional: None = no status
BAUD = 9600

# Camera pins (ESP32-S3-EYE style layout; verified on this board: Camera() returns 57600 bytes).
# The generic firmware has no defaults, so they must be passed in.
CAM_PINS = dict(
    data_pins=[11, 9, 8, 10, 12, 18, 17, 16],
    vsync_pin=6, href_pin=7, pclk_pin=13, xclk_pin=15,
    sda_pin=4, scl_pin=5, xclk_freq=20_000_000,
)

# Printer heat, ESC 7 n1 n2 n3. Higher n2 = darker, slower, more current
HEAT_N1 = 7          # max heated dots, units of 8
HEAT_N2 = 80         # heating time, units of 10 us
HEAT_N3 = 2          # heating interval, units of 10 us

# Bands
BAND_ROWS = 24       # rows per GS v 0 command (24 to 48)
BAND_DELAY_MS = 0    # UART is the bottleneck; raise only if the print garbles

# Frame
FRAME_SIZE = FrameSize.R240X240
FRAME_W, FRAME_H = 240, 240      # must match FRAME_SIZE
ROW_BYTES = 48                   # 384 dots
PAD = "center"                   # "center" or "left"

# Image
DITHER = "fs"        # "threshold" | "bayer" | "fs"
LEVEL = 128          # threshold cutoff
STRETCH_PCT = 1      # contrast stretch: % of pixels clipped at each end. 0 = min/max, None = off

DEBOUNCE_MS = 30
FEED_LINES = 4

# Derived
assert FRAME_W % 8 == 0 and FRAME_W // 8 <= ROW_BYTES, "frame must fit the print row"
X0 = (ROW_BYTES - FRAME_W // 8) // 2 if PAD == "center" else 0   # left margin in bytes
