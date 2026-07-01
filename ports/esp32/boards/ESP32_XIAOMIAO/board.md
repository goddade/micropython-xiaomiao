XueErSi ESP32 XiaoMiao handheld console.

## Hardware

| Peripheral | Pin  | Note                        |
|------------|------|-----------------------------|
| **MCU**    |      | ESP32-WROVER-B, 4MiB Flash, 8MiB PSRAM  |
| **ST7735V**|      | 128x160 TFT, SPI2           |
| TFT_SCK    | 18   |                             |
| TFT_MOSI   | 23   |                             |
| TFT_CS     | 5    |                             |
| TFT_DC     | 4    |                             |
| TFT_RST    | 19   |                             |
| **SD Card**|      | SPI2 (shared SCK/MOSI/MISO) |
| SD_CS      | 22   |                             |
| **Buttons**|      | Active low, internal pull-up|
| KEY_UP     | 2    |                             |
| KEY_DOWN   | 13   |                             |
| KEY_LEFT   | 27   |                             |
| KEY_RIGHT  | 35   |                             |
| KEY_A      | 34   |                             |
| KEY_B      | 12   |                             |
| **Buzzer** | 14   | PWM                         |
| **Light**  | 36   | ADC1_CH0                    |
| **Therm**  | 39   | ADC1_CH3                    |
| **I2C**    |      |                             |
| SCL        | 15   |                             |
| SDA        | 21   |                             |
| **UART0**  |      | Native serial               |
| TX         | 1    |                             |
| RX         | 3    |                             |
| **Extension**|    | PH2.0 3P header             |
| IO25 / DAC | 25   |                             |
| IO26 / DAC | 26   |                             |
| IO32       | 32   |                             |
| IO33       | 33   |                             |

## Built-in Module: `xiaomiao`

The frozen module `xiaomiao` provides pin constants and driver classes:

```python
from xiaomiao import *
```

### Pin Constants

`TFT_MOSI`, `TFT_CLK`, `TFT_CS`, `TFT_DC`, `TFT_RST`,
`SD_CS`, `KEY_UP`, `KEY_DOWN`, `KEY_LEFT`, `KEY_RIGHT`,
`KEY_A`, `KEY_B`, `BUZZER`, `LIGHT`, `THERM`,
`I2C_SCL`, `I2C_SDA`, `IO25`, `IO26`, `IO32`, `IO33`

### Buzzer

```python
buz = Buzzer()
buz.beep()              # 2000Hz, 200ms
buz.tone(1000)          # continuous tone
buz.off()
buz.play([(262, 200), (294, 200), (330, 200)])  # melody
```

### Button

```python
btn = Button(KEY_A)
btn.pressed             # True while held
btn.down_func = lambda: print("pressed")
btn.up_func   = lambda: print("released")
```

By default `use_irq=False`, callbacks fire only when `update()` is called periodically:

```python
while True:
    btn.update()
    time.sleep_ms(10)
```

With `use_irq=True`, callbacks fire automatically on press/release:

```python
btn = Button(KEY_A, use_irq=True)
btn.down_func = lambda: print("pressed")  # fires instantly
```

### ADC Sensors

```python
light = LightSensor()
light.read_percent()    # 0-100%

therm = Thermistor()
therm.read_temp()       # Celsius
```

### micro-gui

This board freezes [micropython-micro-gui](https://github.com/peterhinch/micropython-micro-gui) for a widget-based GUI via ST7735 display and physical buttons.

```python
import hardware_setup
from gui.core.ugui import Screen, ssd
from gui.widgets import Label, Button, CloseButton
from gui.core.writer import CWriter
import gui.fonts.arial10 as arial10
from gui.core.colors import *

class MainScreen(Screen):
    def __init__(self):
        super().__init__()
        wri = CWriter(ssd, arial10, GREEN, BLACK)
        Label(wri, 2, 2, "Hello XiaoMiao!")
        CloseButton(wri)

Screen.change(MainScreen)
```

Button mapping: A=Select, B=Next, UP=Prev, RIGHT=Increase, LEFT=Decrease.

### SD Card

The SD card shares SPI2 with the TFT (SCK=18, MOSI=23, MISO=19) with a dedicated CS pin on GPIO 22.

```python
from xiaomiao import mount_sd
sd = mount_sd()             # mounts to /sd
import os
os.listdir("/sd")
```

Or manually:

```python
import machine, os
sd = machine.SDCard(slot=2, sck=Pin(18), mosi=Pin(23), miso=Pin(19), cs=Pin(22), freq=20000000)
os.mount(sd, "/sd")
```

### ST7735 Display

```python
from xiaomiao import *
from machine import SPI
from st7735_buf import ST7735, RED

spi = SPI(2, baudrate=40000000, polarity=0, phase=0, sck=Pin(TFT_CLK), mosi=Pin(TFT_MOSI))
tft = ST7735(128, 160, spi=spi, res=TFT_RST, dc=TFT_DC, cs=TFT_CS, rotate=1, rgb=True, invert=False)
tft.fill(RED)
tft.show()
```

## Build & Flash

### Prerequisites

Install ESP-IDF (see [ESP-IDF Getting Started](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/)).
Then source the environment:

```bash
source ~/esp/esp-idf/export.sh
```

### Build

```bash
cd ports/esp32
make BOARD=ESP32_XIAOMIAO
```

### Variants

| Variant  | Description                                      |
|----------|--------------------------------------------------|
| (default)| 4MiB flash, 8MiB PSRAM, dual-core                    |
| OTA      | Partition table with OTA support                 |
| D2WD     | ESP32-D2WD chip (2MiB flash)                     |
| UNICORE  | Single-core ESP32 chip                           |

Example with a variant:

```bash
make BOARD=ESP32_XIAOMIAO BOARD_VARIANT=OTA
```

### Flash

```bash
make BOARD=ESP32_XIAOMIAO deploy
```

Or specify the port:

```bash
make BOARD=ESP32_XIAOMIAO PORT=/dev/ttyUSB0 deploy
```
