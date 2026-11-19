# 4D Systems ESP32-P4-70 board bring-up

The purchased model is the 7-inch non-touch ESP32-P4-70. The manufacturer specifies a 1280×800 landscape IPS LCD, 1,000 cd/m² at its maximum contrast setting, an ESP32-P4NRW32 with 32 MB PSRAM, 32 MB external Quad SPI NOR flash, and an onboard microSD slot. The LCD runs natively at 800×1280. The rev 1.4 schematic shows a separate 40-contact LCD flex socket carrying two data pairs, one clock pair, power, reset and backlight. The 30-pin user FFC and 30-pin H4 header serve external peripherals. [4D Systems series datasheet R1.1, pp. 8–13, 55, 58](https://resources.4dsystems.com.au/datasheets/esp32p4/esp32-p4-series/ESP32-P4_Series_Datasheet_R_1_1.pdf)

## Native build baseline

| Layer | Pin and basis |
|---|---|
| ESP-IDF | `v5.5.5`, commit `b774170ff46c393eeb5e495ea37936038d3f4f4f`, target `esp32p4`. 4D's LCD manifest accepts >=5.5.2. 5.5.5 supports selecting both silicon families. [ESP-IDF release](https://github.com/espressif/esp-idf/releases/tag/v5.5.5) · [4D manifest](https://github.com/4dsystems/esp32p4_lcd/blob/f4f001f7493f263dcf00c4459bb4079395dcce71/idf_component.yml) |
| 4D display driver | `4dsystems/esp32p4_lcd ==0.1.1`, source commit `f4f001f7493f263dcf00c4459bb4079395dcce71`. Its manifest pulls JD9365 `^2.0.2` and GT911 `^1.2.1`. Select the non-touch variant and omit touch initialization. [Registry package](https://components.espressif.com/components/4dsystems/esp32p4_lcd/versions/0.1.1/readme) · [Source Kconfig](https://github.com/4dsystems/esp32p4_lcd/blob/f4f001f7493f263dcf00c4459bb4079395dcce71/Kconfig) |
| LVGL integration | `lvgl/lvgl ==9.5.0` and `espressif/esp_lvgl_port ==2.7.0` are proposed pins. The IDF v5.5.5 DSI example uses LVGL 9.5.0. Port 2.7.0 accepts IDF >=5.1 and LVGL >=8,<10 and provides an ESP32-P4 DSI registration path. The 4D driver has no LVGL dependency, so its manifest establishes no vendor LVGL version. [IDF example manifest](https://github.com/espressif/esp-idf/blob/v5.5.5/examples/peripherals/lcd/mipi_dsi/main/idf_component.yml) · [Port manifest](https://github.com/espressif/esp-bsp/blob/d15cf39696339b128eceb75665d806d8bd10959a/components/esp_lvgl_port/idf_component.yml) |

The local vendor source checkouts are `4dsystems-esp32p4_lcd` and `4dsystems-GFX4dESP32P4` under `~/TunerStudioProjects/TurboExo-deps/research/`.

Keep the resolved component lockfile. Select `CONFIG_ESP32P4_LCD_70=y`, `CONFIG_ESP32P4_LCD_NOTOUCH=y`, `CONFIG_SPIRAM=y`, and `CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y`. Start from the ESP32-P4 DSI example's PSRAM settings, which select hex mode at 200 MHz, and verify the detected PSRAM at boot. Set flash size and the partition table for the board's 32 MB flash. [4D header and Kconfig](https://github.com/4dsystems/esp32p4_lcd/tree/f4f001f7493f263dcf00c4459bb4079395dcce71) · [ESP-IDF DSI PSRAM defaults](https://github.com/espressif/esp-idf/blob/v5.5.5/examples/peripherals/lcd/mipi_dsi/sdkconfig.defaults.esp32p4) · [Espressif console](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32p4/api-guides/usb-serial-jtag-console.html)

Read the delivered SoC revision via the ROM download connection before choosing the firmware profile. On IDF 5.5.5, set `CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y` for pre-v3 silicon and `n` for v3.x. The rev 1.4 board schematic marks chip pin 54 NC, which is consistent with the pre-v3 reference design. Explicitly set `CONFIG_ESP32P4_REV_MIN_0=y` in the pre-v3 profile and `CONFIG_ESP32P4_REV_MIN_300=y` in the v3 profile. IDF 5.5.5 otherwise defaults v3 minimum to 3.1 and rejects revision 3.0. The delivered unit's PCB and chip revisions still need confirmation. Espressif documents separate firmware images for the two chip families. [Rev 1.4 schematic, p. 55](https://resources.4dsystems.com.au/datasheets/esp32p4/esp32-p4-series/ESP32-P4_Series_Datasheet_R_1_1.pdf#page=55) · [Espressif chip revision guide](https://documentation.espressif.com/esp32-p4-chip-revision-v3.x_user_guide_en.pdf)

## Display initialization and first image

Use `esp32p4_lcd_full_init(&panel)`. It acquires P4 LDO channel 3 at 2,500 mV, sets up DSI bus 0 with two 1,200 Mbps lanes, opens the DBI command channel at virtual channel 0 with 8-bit commands and parameters, and resets and starts the JD9365 using the 7-inch command table. RGB565 input and output run at a 60 MHz DPI clock. The HSync pulse/back/front timings are 20/20/40 and the VSync values are 4/12/30. That is about 51.4 Hz from 60 MHz ÷ (880 × 1,326). LCD reset is GPIO23. The SY7023 backlight driver takes active-high PWM on GPIO22. The 4D component uses 25 kHz LEDC with brightness 0–255 and starts the output dark unless auto-on is selected. [4D implementation](https://github.com/4dsystems/esp32p4_lcd/blob/f4f001f7493f263dcf00c4459bb4079395dcce71/esp32p4_lcd.c) · [Timing and pins](https://github.com/4dsystems/esp32p4_lcd/blob/f4f001f7493f263dcf00c4459bb4079395dcce71/include/mipi_lcd.h) · [7-inch init table](https://github.com/4dsystems/esp32p4_lcd/blob/f4f001f7493f263dcf00c4459bb4079395dcce71/include/mipi_init.h#L5)

The manufacturer publishes the board's IDF component and a native wrapper example in its README. Its registry entry has zero complete projects. The manufacturer's Workshop/Arduino `NonTouchTemplate` is a board-specific sanity sketch, tested by 4D with Arduino ESP32 Core 3.3.7. For native bring-up, a minimal `app_main` with the 4D component above is enough for a DSI transport test. The ESP-IDF MIPI DSI example supplies the LVGL and display callback references. Its board-specific panel setup targets Espressif's evaluation boards. [4D IDF component](https://components.espressif.com/components/4dsystems/esp32p4_lcd/versions/0.1.1/readme) · [4D NonTouchTemplate](https://github.com/4dsystems/GFX4dESP32P4/blob/2e9936f4db706e2abe2368ba8ccbc18a1f1e0435/examples/NonTouchTemplate/NonTouchTemplate.ino) · [ESP-IDF DSI example](https://github.com/espressif/esp-idf/tree/v5.5.5/examples/peripherals/lcd/mipi_dsi)

```c
#include "esp32p4_lcd.h"

void app_main(void)
{
    esp_lcd_panel_handle_t panel = NULL;
    ESP_ERROR_CHECK(esp32p4_lcd_full_init(&panel));
    ESP_ERROR_CHECK(esp_lcd_dpi_panel_set_pattern(panel, MIPI_DSI_PATTERN_BAR_VERTICAL));
    ESP_ERROR_CHECK(esp32p4_lcd_backlight_set(128));
}
```

For LVGL, disable the test pattern and register the vendor panel with `lvgl_port_add_disp_dsi()` at 800×1280 RGB565. Port 2.7.0's DSI path accepts a zero-initialized `io_handle` because it registers completion callbacks on the DPI panel handle. Start with one DPI scanout framebuffer and partial LVGL draw buffers, enable `sw_rotate`, then call `lv_display_set_rotation()` for a logical 1280×800 display. Check upright text and labeled corners to choose 90° or 270° for the mounted panel. Port 2.7.0 uses PPA for rotation when `CONFIG_LVGL_PORT_ENABLE_PPA=y`. Its `avoid_tearing` path requires two full panel buffers, so evaluate it after the initial partial-render rotation works. One full RGB565 frame uses 2,048,000 bytes. Confirm orientation, color, redraw performance and tearing with the real panel. [Espressif port DSI and rotation code](https://github.com/espressif/esp-bsp/blob/d15cf39696339b128eceb75665d806d8bd10959a/components/esp_lvgl_port/src/lvgl9/esp_lvgl_port_disp.c) · [Port PPA Kconfig](https://github.com/espressif/esp-bsp/blob/d15cf39696339b128eceb75665d806d8bd10959a/components/esp_lvgl_port/Kconfig)

## Connectors and GPIO

The H4 pins below use the manufacturer's numbered header diagram. GPIO signals are 3.3 V. **UART1, buttons and external I²C are proposed project mappings** based on free pins in the rev 1.4 schematic. Verify the purchased board and the telemetry adapter's voltage levels before connecting the ECU. [4D pinout and rev 1.4 schematic, pp. 8–10, 55](https://resources.4dsystems.com.au/datasheets/esp32p4/esp32-p4-series/ESP32-P4_Series_Datasheet_R_1_1.pdf)

| Function | Board connection |
|---|---|
| Telemetry UART1 | P4 TX GPIO17 (H4 pin 23) and P4 RX GPIO18 (H4 pin 24). Signal ground H4 pin 3 or 4. Route via the GPIO matrix. Cross TX/RX at a compatible 3.3 V interface. |
| External buttons | GPIO19 (H4 pin 21), GPIO20 (H4 pin 22) and GPIO21 (H4 pin 19) are candidates for active-low switches to ground with pull-ups and firmware debounce. |
| Optional ADS1115 | External I²C SDA GPIO15 (H4 pin 25) and SCL GPIO16 (H4 pin 26), with a common ground and bus pull-ups to 3.3 V. Use an unused high-performance I²C controller. Board I²C GPIO7/8 are internal and absent from H4 and the user FFC. Leave the fuel-level and oil-temperature inputs disabled until their sender circuits and calibration are verified. |
| Onboard BOOT and RESET | BOOT asserts the GPIO35 strap. RES pulls the chip enable line low. Preserve both for recovery. |
| USB-PROG | Direct USB Serial/JTAG on GPIO24 D− and GPIO25 D+. Use this port for programming, monitoring and JTAG. The separate `USB` receptacle is the OTG port. |
| UART0 recovery | 30-pin user FFC pin 23 is GPIO38 RX and pin 24 is GPIO37 TX, as shown in the schematic and connector pin table. The series text's GPIO39 UART claim conflicts with both and GPIO39 is wired to microSD D0. FFC pin 19 carries BOOT and pin 22 carries ESP-EN for the 4D-UPA programmer. |
| microSD | SDMMC slot 1, CLK GPIO43, CMD GPIO44, D0–D3 GPIO39–42, active-low card power enable GPIO45 and card detect GPIO46. The schematic shows a gate pulldown on the P-channel power switch and a pull-up on the card-detect switch, whose other contact is grounded. SD signal pull-ups are on ESP-LDO-VO4. Verify that domain and card-detect behavior when implementing SD. |
| Other onboard uses | GPIO4/5 are touch reset/interrupt connections and GPIO7/8 are shared board I²C. GPIO9–13 carry audio I²S and GPIO53 controls the amplifier. The base board requires external hardware for Wi-Fi or Bluetooth. 4D sells an optional C6 add-on for the H4 connector. |

[4D Arduino SD pin setup](https://github.com/4dsystems/GFX4dESP32P4/blob/2e9936f4db706e2abe2368ba8ccbc18a1f1e0435/src/gfx4desp32P4.cpp#L178) · [Espressif USB Serial/JTAG docs](https://docs.espressif.com/projects/esp-idf/en/v5.5.5/esp32p4/api-guides/usb-serial-jtag-console.html)

## Power and bench confirmation

Use regulated 5 V nominal. The published operating input range is 4–6 V and the non-touch 7-inch model draws 865 mA typical at 5 V and maximum specified brightness under 4D's simple-display test conditions. Bench supply sizing needs margin above that figure. H3 selects USB VBUS (center-right) or the H1 DC terminal (center-left), viewed as shown in the datasheet. H1 positive is on the right in that view. The H4 and user FFC power pins connect directly to the 5 V rail and bypass H3. The USB receptacles share a VBUS supply. For powered bench debug, use H1 with H3 set to DC if USB power is insufficient, and connect a data cable to USB-PROG. [4D datasheet, pp. 16, 56–57](https://resources.4dsystems.com.au/datasheets/esp32p4/esp32-p4-series/ESP32-P4_Series_Datasheet_R_1_1.pdf)

Bench confirmation remains open for USB enumeration and chip revision, color bars, landscape orientation, brightness, frame timing, the UART link, buttons and optional SD. This research pass verified the published source and schematic. Compilation and target execution of the sample remain open.
