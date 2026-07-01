import gc
import framebuf
from struct import pack
from machine import Pin
from micropython import const
from time import sleep_us, sleep_ms

SWRESET = const(0x01)
SLPOUT = const(0x11)
NORON = const(0x13)

INVOFF = const(0x20)
INVON = const(0x21)
DISPON = const(0x29)
CASET = const(0x2A)
RASET = const(0x2B)
RAMWR = const(0x2C)
MADCTL = const(0x36)
COLMOD = const(0x3A)

FRMCTR1 = const(0xB1)
FRMCTR2 = const(0xB2)
FRMCTR3 = const(0xB3)

INVCTR = const(0xB4)

PWCTR1 = const(0xC0)
PWCTR2 = const(0xC1)
PWCTR3 = const(0xC2)
PWCTR4 = const(0xC3)
PWCTR5 = const(0xC4)
VMCTR1 = const(0xC5)

BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_POS = ">HH"

GMCTRP1 = const(0xE0)
GMCTRN1 = const(0xE1)

SCREEN_128X160 = [(128, 160, 0, 0),
                  (160, 128, 0, 0),
                  (128, 160, 0, 0),
                  (160, 128, 0, 0),
                  (128, 160, 0, 0),
                  (160, 128, 0, 0),
                  (128, 160, 0, 0)]
SCREEN_128X128 = [(128, 128, 2, 1),
                  (128, 128, 1, 2),
                  (128, 128, 2, 3),
                  (128, 128, 3, 2),
                  (128, 128, 2, 1),
                  (128, 128, 1, 2),
                  (128, 128, 2, 3)]
SCREEN_80X160 = [(80, 160, 26, 1),
                 (160, 80, 1, 26),
                 (80, 160, 26, 1),
                 (160, 80, 1, 26),
                 (80, 160, 26, 1),
                 (160, 80, 1, 26),
                 (80, 160, 26, 1)]

ROTATIONS = [0x00, 0x60, 0xC0, 0xA0, 0x40, 0x20, 0x80]


def _encode_pos(x, y):
    return pack(_ENCODE_POS, x, y)


class ST7735(framebuf.FrameBuffer):
    def __init__(self, width: int, height: int, spi, res: int, dc: int,
                 cs: int = None, rotate: int = 0, rgb: bool = True, invert: bool = True):
        self.width = width
        self.height = height
        self.x_start = 0
        self.y_start = 0
        self.spi = spi
        self.res = Pin(res, Pin.OUT, Pin.PULL_DOWN)
        self.dc = Pin(dc, Pin.OUT, Pin.PULL_DOWN)
        if cs is None:
            self.cs = int
        else:
            self.cs = Pin(cs, Pin.OUT, Pin.PULL_DOWN)
        self._rotate = rotate
        self._rgb = rgb
        self.hard_reset()
        self.soft_reset()
        self.poweron()

        sleep_us(300)
        self._write(FRMCTR1, bytearray([0x01, 0x2C, 0x2D]))
        self._write(FRMCTR2, bytearray([0x01, 0x2C, 0x2D]))
        self._write(FRMCTR3, bytearray([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D]))
        sleep_us(10)
        self._write(INVCTR, bytearray([0x07]))
        self._write(PWCTR1, bytearray([0xA2, 0x02, 0x84]))
        self._write(PWCTR2, bytearray([0xC5]))
        self._write(PWCTR3, bytearray([0x0A, 0x00]))
        self._write(PWCTR4, bytearray([0x8A, 0x2A]))
        self._write(PWCTR5, bytearray([0x8A, 0xEE]))
        self._write(VMCTR1, bytearray([0x0E]))

        self._write(COLMOD, bytearray([0x05]))
        sleep_ms(50)
        gc.collect()
        self.buffer = bytearray(self.height * self.width * 2)
        self.rotate(self._rotate)
        self.invert(invert)
        sleep_ms(10)
        self.write_cmd(GMCTRP1)
        self.write_data(
            bytearray([0x02, 0x1c, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2d, 0x29, 0x25, 0x2b, 0x39, 0x00, 0x01, 0x03, 0x10]))
        self.write_cmd(GMCTRN1)
        self.write_data(
            bytearray([0x03, 0x1d, 0x07, 0x06, 0x2e, 0x2c, 0x29, 0x2d, 0x2e, 0x2e, 0x37, 0x3f, 0x00, 0x00, 0x02, 0x10]))
        self.write_cmd(NORON)
        sleep_us(10)
        self.write_cmd(DISPON)
        sleep_ms(100)
        self.clear()
        self.show()

    def _write(self, command=None, data=None):
        self.cs(0)
        if command is not None:
            self.dc(0)
            self.spi.write(bytes([command]))
        if data is not None:
            self.dc(1)
            self.spi.write(data)
        self.cs(1)

    def write_cmd(self, cmd):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytes([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.cs(0)
        self.dc(1)
        self.spi.write(data)
        self.cs(1)

    def hard_reset(self):
        self.cs(0)
        self.res(1)
        sleep_ms(50)
        self.res(0)
        sleep_ms(50)
        self.res(1)
        sleep_ms(150)
        self.cs(1)

    def soft_reset(self):
        self._write(SWRESET)
        sleep_ms(150)

    def poweron(self):
        self._write(SLPOUT)

    def invert(self, value):
        if value:
            self._write(INVON)
        else:
            self._write(INVOFF)

    def rotate(self, rotate):
        self._rotate = rotate
        madctl = ROTATIONS[rotate]
        if (self.width == 160 and self.height == 80) or (self.width == 80 and self.height == 160):
            table = SCREEN_80X160
        elif (self.width == 160 and self.height == 128) or (self.width == 128 and self.height == 160):
            table = SCREEN_128X160
        elif self.width == 128 and self.height == 128:
            table = SCREEN_128X128
        else:
            raise ValueError(
                "Unsupported display. 128x160, 128x128 and 80x160 are supported."
            )

        self.width, self.height, self.x_start, self.y_start = table[rotate]
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565, self.width)
        self._write(MADCTL, bytes([madctl | (0x00 if self._rgb else 0x08)]))

    def _set_columns(self, start, end):
        if start <= end <= self.width:
            self._write(CASET, _encode_pos(
                start + self.x_start, end + self.x_start))

    def _set_rows(self, start, end):
        if start <= end <= self.height:
            self._write(RASET, _encode_pos(
                start + self.y_start, end + self.y_start))

    def set_window(self, x0, y0, x1, y1):
        if x0 < self.width and y0 < self.height:
            self._set_columns(x0, x1)
            self._set_rows(y0, y1)
            self._write(RAMWR)

    def clear(self):
        self.fill(0)

    def show(self):
        self.set_window(0, 0, self.width - 1, self.height - 1)
        mv = memoryview(self.buffer)
        for i in range(0, len(self.buffer), 2):
            mv[i], mv[i + 1] = mv[i + 1], mv[i]
        self._write(RAMWR, self.buffer)
        for i in range(0, len(self.buffer), 2):
            mv[i], mv[i + 1] = mv[i + 1], mv[i]

    @staticmethod
    def color(r, g, b):
        return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3
