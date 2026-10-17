"""Run dither.py and printer.py on CPython: fake micropython, machine, camera, sleep_ms.
Viper is the identity decorator, so these tests check the algorithm, not viper compilation."""
import builtins, pathlib, sys, time, types

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

mp = types.ModuleType("micropython")
mp.viper = lambda f: f
mp.const = lambda x: x
sys.modules["micropython"] = mp
builtins.ptr8 = builtins.ptr16 = builtins.ptr32 = lambda x: x

cam = types.ModuleType("camera")
cam.FrameSize = types.SimpleNamespace(R240X240=5)
sys.modules["camera"] = cam

time.sleep_ms = lambda ms: None
time.ticks_ms = lambda: int(time.monotonic() * 1000)
time.ticks_diff = lambda a, b: a - b


class UART:
    def __init__(self, *a, **kw):
        self.kw, self.sent = kw, []

    def write(self, data):
        self.sent.append(bytes(data))

    def flush(self):
        pass

    def any(self):
        return 0


mach = types.ModuleType("machine")
mach.UART = UART
sys.modules["machine"] = mach
