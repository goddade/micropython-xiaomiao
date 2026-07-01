import gc
from machine import Pin, SPI
from xiaomiao import KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_A, KEY_B, TFT_MOSI, TFT_CLK, TFT_CS, TFT_DC, TFT_RST

from drivers.st7735v.st7735v import ST7735V as SSD

pdc = Pin(TFT_DC, Pin.OUT, value=0)
pcs = Pin(TFT_CS, Pin.OUT, value=1)
prst = Pin(TFT_RST, Pin.OUT, value=1)
spi = SPI(2, baudrate=30_000_000, sck=Pin(TFT_CLK), mosi=Pin(TFT_MOSI))
gc.collect()
ssd = SSD(spi, pcs, pdc, prst, height=160, width=128, rotate=1)

from gui.core.ugui import Display

# D-pad: UP/DOWN navigate, LEFT/RIGHT adjust. A selects. B is unused.
nxt = Pin(KEY_DOWN, Pin.IN, Pin.PULL_UP)    # Down → next widget
sel = Pin(KEY_A, Pin.IN)                    # A → select (GPIO34, input-only, external pull-up required)
prev = Pin(KEY_UP, Pin.IN, Pin.PULL_UP)     # Up → previous widget
increase = Pin(KEY_RIGHT, Pin.IN)           # Right → increase value (GPIO35, input-only, external pull-up required)
decrease = Pin(KEY_LEFT, Pin.IN, Pin.PULL_UP) # Left → decrease value
display = Display(ssd, nxt, sel, prev, increase, decrease)
