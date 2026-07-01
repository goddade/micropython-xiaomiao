from machine import Pin, ADC, PWM
from micropython import const
import math, time

# ========== Pin Map ==========

# Display (ST7735, SPI2)
TFT_MOSI = const(23)
TFT_CLK  = const(18)
TFT_CS   = const(5)
TFT_DC   = const(4)
TFT_RST  = const(19)

# SD Card (SPI2, shared with TFT)
SD_CS    = const(22)

# Buttons (active low, internal pull-up)
KEY_UP   = const(2)
KEY_DOWN = const(13)
KEY_LEFT = const(27)
KEY_RIGHT= const(35)
KEY_A    = const(34)
KEY_B    = const(12)

# Buzzer (PWM via LEDC)
BUZZER   = const(14)

# ADC Sensors
LIGHT    = const(36)
THERM    = const(39)

# I2C
I2C_SCL  = const(15)
I2C_SDA  = const(21)

# Extension IOs (PH2.0 3P header, also DAC)
IO25     = const(25)
IO26     = const(26)
IO32     = const(32)
IO33     = const(33)


# ========== Buzzer ==========

class Buzzer:
    def __init__(self, pin=BUZZER):
        self.pwm = PWM(Pin(pin, Pin.OUT), freq=2000, duty=0)

    def tone(self, freq, duty=512):
        self.pwm.freq(freq)
        self.pwm.duty(duty)

    def beep(self, freq=2000, ms=200):
        self.tone(freq)
        time.sleep_ms(ms)
        self.off()

    def off(self):
        self.pwm.duty(0)

    def play(self, notes, tempo=150):
        for f, d in notes:
            self.tone(f)
            time.sleep_ms(d)
            self.off()
            time.sleep_ms(tempo)


# ========== Button ==========

class Button:
    def __init__(self, pin, use_irq=False):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._down_func = None
        self._up_func = None
        self._use_irq = use_irq
        self._last = self.pin.value()
        if use_irq:
            self.pin.irq(handler=self._irq, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

    def _irq(self, pin):
        v = pin.value()
        if v == 0:
            if self._down_func:
                self._down_func()
        else:
            if self._up_func:
                self._up_func()

    def update(self):
        if self._use_irq:
            return
        v = self.pin.value()
        if self._last == 1 and v == 0:
            if self._down_func:
                self._down_func()
        elif self._last == 0 and v == 1:
            if self._up_func:
                self._up_func()
        self._last = v

    @property
    def value(self):
        return self.pin.value()

    @property
    def pressed(self):
        return self.pin.value() == 0

    @property
    def down_func(self):
        return self._down_func

    @down_func.setter
    def down_func(self, f):
        self._down_func = f

    @property
    def up_func(self):
        return self._up_func

    @up_func.setter
    def up_func(self, f):
        self._up_func = f


# ========== ADC Sensor ==========

class ADCSensor:
    def __init__(self, pin, atten=ADC.ATTN_11DB):
        self.adc = ADC(Pin(pin))
        self.adc.atten(atten)

    def read_raw(self):
        return self.adc.read()

    def read_voltage(self):
        return self.adc.read() / 4095 * 3.3


class LightSensor(ADCSensor):
    def __init__(self):
        super().__init__(LIGHT)

    def read_percent(self):
        return self.adc.read() / 4095 * 100


class Thermistor(ADCSensor):
    BETA = const(3950)
    R_REF = const(10000)
    T_REF = const(25)

    def __init__(self):
        super().__init__(THERM)

    def read_resistance(self):
        v = self.read_voltage()
        if v >= 3.3:
            return float('inf')
        return self.R_REF * v / (3.3 - v)

    def read_temp(self):
        r = self.read_resistance()
        if r == float('inf'):
            return float('nan')
        inv_t = 1.0 / (self.T_REF + 273.15) + math.log(r / self.R_REF) / self.BETA
        return 1.0 / inv_t - 273.15


# ========== Board Init (optional LVGL) ==========

def init():
    try:
        import lvgl as lv
    except ImportError:
        raise RuntimeError("LVGL not available; install lv_binding_micropython")
    lv.init()
    from machine import SPI
    from st7735_buf import ST7735, RAMWR

    spi = SPI(2, baudrate=40000000, polarity=0, phase=0, sck=Pin(TFT_CLK), mosi=Pin(TFT_MOSI), miso=None)
    tft = ST7735(128, 160, spi=spi, res=TFT_RST, dc=TFT_DC, cs=TFT_CS, rotate=1, rgb=True, invert=False)

    buf = bytearray(160 * 128 * 2)

    def flush(disp_drv, area, color_p):
        w = area.x2 - area.x1 + 1
        h = area.y2 - area.y1 + 1
        stride = 160 * 2
        tft._set_columns(area.x1, area.x2)
        tft._set_rows(area.y1, area.y2)
        mv = memoryview(buf)
        data = bytearray(w * h * 2)
        for r in range(h):
            src = (area.y1 + r) * stride + area.x1 * 2
            dst = r * w * 2
            for i in range(0, w * 2, 2):
                data[dst + i] = mv[src + i + 1]
                data[dst + i + 1] = mv[src + i]
        tft.cs(0)
        tft.dc(0)
        tft.spi.write(bytes([RAMWR]))
        tft.dc(1)
        tft.spi.write(data)
        tft.cs(1)
        disp_drv.flush_ready()

    disp = lv.display_create(160, 128)
    disp.set_flush_cb(flush)
    disp.set_buffers(buf, None, len(buf), lv.DISPLAY_RENDER_MODE.PARTIAL)
    return tft


def mount_sd(mount_point="/sd"):
    import machine, os
    sd = machine.SDCard(slot=2, sck=Pin(TFT_CLK), mosi=Pin(TFT_MOSI), miso=Pin(19), cs=Pin(SD_CS), freq=20000000)
    os.mount(sd, mount_point)
    return sd
