from time import sleep_us, sleep_ms
import framebuf
import gc
import micropython
from drivers.boolpalette import BoolPalette


class ST7735V(framebuf.FrameBuffer):
    @staticmethod
    def rgb(r, g, b):
        return (r & 0xf8) << 8 | (g & 0xfc) << 3 | b >> 3

    def __init__(self, spi, cs, dc, rst, height=128, width=160, usd=False, init_spi=False, rotate=0):
        self._spi = spi
        self._rst = rst
        self._dc = dc
        self._cs = cs
        self._spi_init = init_spi
        self.palette = BoolPalette(framebuf.RGB565)
        if rotate:
            usd = False
            r = rotate & 3
        else:
            r = 2 if usd else 0
        if r in (0, 2):
            self.height = height
            self.width = width
        else:
            self.height = width
            self.width = height
        gc.collect()
        n = self.height * self.width * 2
        self._draw_buf = bytearray(n)
        self._disp_buf = bytearray(n)
        self._mvb = memoryview(self._draw_buf)
        self._disp_mv = memoryview(self._disp_buf)
        super().__init__(self._draw_buf, self.width, self.height, framebuf.RGB565)
        self._init(r)
        self.show()

    def _wcmd(self, cmd):
        self._dc(0)
        self._cs(0)
        self._spi.write(cmd)
        self._cs(1)

    def _wcd(self, cmd, data):
        self._dc(0)
        self._cs(0)
        self._spi.write(cmd)
        self._cs(1)
        self._dc(1)
        self._cs(0)
        self._spi.write(data)
        self._cs(1)

    def _init(self, r):
        self._dc(0)
        self._rst(1)
        sleep_ms(50)
        self._rst(0)
        sleep_ms(50)
        self._rst(1)
        sleep_ms(150)
        self._cs(1)
        if self._spi_init:
            self._spi_init(self._spi)
        self._wcmd(b'\x01')
        sleep_ms(150)
        self._wcmd(b'\x11')
        self._wcd(b'\xb1', b'\x01\x2C\x2D')
        self._wcd(b'\xb2', b'\x01\x2C\x2D')
        self._wcd(b'\xb3', b'\x01\x2C\x2D\x01\x2C\x2D')
        sleep_us(10)
        self._wcd(b'\xb4', b'\x07')
        self._wcd(b'\xc0', b'\xa2\x02\x84')
        self._wcd(b'\xc1', b'\xc5')
        self._wcd(b'\xc2', b'\x0a\x00')
        self._wcd(b'\xc3', b'\x8a\x2a')
        self._wcd(b'\xc4', b'\x8a\xee')
        self._wcd(b'\xc5', b'\x0e')
        self._wcd(b'\x3a', b'\x05')
        sleep_ms(50)
        madctl = (0x00, 0x60, 0xc0, 0xa0)[r]
        self._wcd(b'\x36', bytes([madctl]))
        self._wcd(b'\xe0', b'\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2B\x39\x00\x01\x03\x10')
        self._wcd(b'\xe1', b'\x03\x1d\x07\x06\x2E\x2C\x29\x2D\x2E\x2E\x37\x3F\x00\x00\x02\x10')
        self._wcd(b'\x2a', int.to_bytes(self.width, 4, 'big'))
        self._wcd(b'\x2b', int.to_bytes(self.height, 4, 'big'))
        self._wcmd(b'\x13')
        sleep_us(10)
        self._wcmd(b'\x29')
        sleep_ms(100)
        self.fill(0)
        self.show()

    @micropython.viper
    def _swap_bytes(self):
        src = ptr8(self._draw_buf)
        dst = ptr8(self._disp_buf)
        n = int(len(self._draw_buf))
        i = int(0)
        while i < n:
            dst[i] = src[i + 1]
            dst[i + 1] = src[i]
            i += 2

    def show(self):
        self._dc(0)
        self._cs(0)
        if self._spi_init:
            self._spi_init(self._spi)
        self._spi.write(b'\x2c')
        self._dc(1)
        self._swap_bytes()
        self._spi.write(self._disp_buf)
        self._cs(1)
