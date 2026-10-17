# Wiring/baud check: text, then the DC2 T self-test page. 9600 first, then 19200.
# Read the paper: the baud whose text is readable is the one that works.
from time import sleep_ms
from printer import DP_EH600

for baud in (9600, 19200):
    p = DP_EH600(baud)
    p.init()
    p.print_text("baud %d: hello" % baud)
    p.self_test()
    sleep_ms(4000)
    print(baud, "status:", repr(p.status()), "(None = no reply or RX not wired)")
