#include "platform.hpp"

#include <algorithm>
#include <array>

#include "cluster/protocol.hpp"
#include "driver/uart.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "hal/uart_ll.h"

namespace cluster::platform {
namespace {

constexpr char kTag[] = "cluster_uart";
constexpr uart_port_t kPort = UART_NUM_1;
constexpr int kRxBufferBytes = 512;
constexpr unsigned kEventCapacity = 32;
constexpr uint32_t kRxErrorInterrupts = UART_INTR_RXFIFO_OVF | UART_INTR_BRK_DET |
                                        UART_INTR_PARITY_ERR | UART_INTR_FRAM_ERR;
constexpr unsigned kRxFsmIdle = 0;
QueueHandle_t uart_events = nullptr;
QueueHandle_t telemetry_queue = nullptr;
TaskHandle_t uart_task = nullptr;

struct UartStartup {
    SemaphoreHandle_t complete;
    esp_err_t result = ESP_FAIL;
};

ClientConfig client_config()
{
    ClientConfig config;
#ifdef CONFIG_CLUSTER_ECU_VSS
    config.vss_enabled = true;
#endif
#ifdef CONFIG_CLUSTER_ECU_OIL_PRESSURE
    config.oil_enabled = true;
    config.oil_calibrated = true;
#endif
    config.ego_delay_ms = CONFIG_CLUSTER_EGO_DELAY_MS;
    return config;
}

bool check_receive_errors(TelemetryClient& client)
{
    uart_event_t event{};
    bool receive_error = false;
    unsigned n = 0;
    for (; n < kEventCapacity && xQueueReceive(uart_events, &event, 0); ++n) {
        switch (event.type) {
        case UART_FIFO_OVF:
        case UART_BUFFER_FULL:
        case UART_BREAK:
        case UART_PARITY_ERR:
        case UART_FRAME_ERR:
            receive_error = true;
            break;
        default:
            break;
        }
    }
    // At capacity the ISR could have dropped an error event.
    if (receive_error || n == kEventCapacity) {
        client.transport_error(now_ms());
        uart_flush_input(kPort);
        return false;
    }
    return true;
}

// Bound the work per pass. Any remainder is checked before advancing the client.
bool drain_receive(TelemetryClient& client)
{
    std::array<uint8_t, kRxBufferBytes> rx{};
    const int received = uart_read_bytes(kPort, rx.data(), rx.size(), 0);
    if (received < 0) {
        client.transport_error(now_ms());
        return false;
    }
    if (received > 0) {
        client.receive(rx.data(), static_cast<size_t>(received), now_ms());
    }
    return true;
}

bool receive_is_quiet(TelemetryClient& client)
{
    // Sample RXD before the FSM: a just-started low bit may not yet have
    // advanced the FSM. If preempted until a high data bit, the following FSM
    // sample catches the in-flight byte; the FIFO then catches completion.
    uart_dev_t* const hw = UART_LL_GET_HW(kPort);
    if (hw->status.rxd == 0 || hw->fsm_status.st_urx_out != kRxFsmIdle ||
        uart_ll_get_rxfifo_len(hw) != 0 ||
        (uart_ll_get_intsts_mask(hw) & kRxErrorInterrupts) != 0) {
        return false;
    }

    // The ISR runs on this core. If it moved data or cleared an error before
    // the hardware sample, its ring and event writes finished before this
    // task resumed. A byte still awaiting an RX timeout stays visible above.
    size_t pending = 0;
    if (uart_get_buffered_data_len(kPort, &pending) != ESP_OK) {
        client.transport_error(now_ms());
        return false;
    }
    return pending == 0 && uxQueueMessagesWaiting(uart_events) == 0;
}

bool write_and_wait(const TxRequest& request)
{
    // There is one writer and no TX ring. A short FIFO write is uncertain,
    // even if the queued prefix later drains successfully.
    const int written = uart_tx_chars(kPort, reinterpret_cast<const char*>(request.bytes.data()),
                                      request.size);
    const esp_err_t result = uart_wait_tx_done(kPort, pdMS_TO_TICKS(10));
    return written == static_cast<int>(request.size) && result == ESP_OK;
}

esp_err_t configure_uart()
{
    uart_config_t config{};
    config.baud_rate = 115200;
    config.data_bits = UART_DATA_8_BITS;
    config.parity = UART_PARITY_DISABLE;
    config.stop_bits = UART_STOP_BITS_1;
    config.flow_ctrl = UART_HW_FLOWCTRL_DISABLE;
    config.source_clk = UART_SCLK_DEFAULT;
    ESP_RETURN_ON_ERROR(uart_param_config(kPort, &config), kTag, "UART configuration failed");
    ESP_RETURN_ON_ERROR(uart_set_pin(kPort, kEcuTx, kEcuRx, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE),
                        kTag, "UART pin configuration failed");
    ESP_RETURN_ON_ERROR(uart_set_rx_timeout(kPort, 2), kTag, "UART RX timeout configuration failed");
    // The driver's default mask leaves frame error reporting disabled.
    return uart_enable_intr_mask(kPort, UART_INTR_FRAM_ERR);
}

void run_uart(void* argument)
{
    auto& startup = *static_cast<UartStartup*>(argument);
    // IDF allocates the UART interrupt on the installing task's CPU. The
    // pinned worker installs it so its own buffer checks cannot overlap the ISR.
    esp_err_t err = uart_driver_install(kPort, kRxBufferBytes, 0, kEventCapacity, &uart_events, 0);
    if (err == ESP_OK) {
        err = configure_uart();
        if (err != ESP_OK) {
            uart_driver_delete(kPort);
        }
    }
    startup.result = err;
    xSemaphoreGive(startup.complete);
    if (err != ESP_OK) {
        vTaskDelete(nullptr);
        return;
    }

    TelemetryClient client(client_config());
    Snapshot latest{};
    while (true) {
        if (ulTaskNotifyTake(pdTRUE, 0) != 0) {
            client.confirm_ecu_reset(now_ms());
        }
        if (check_receive_errors(client) && drain_receive(client)) {
            // If tick may complete a guard, the hardware sample must follow
            // the tick timestamp. The same check gates startup and recovery TX.
            const uint64_t tick_ms = now_ms();
            const TxRequest request = receive_is_quiet(client) ? client.tick(tick_ms) : TxRequest{};
            if (request.size != 0) {
                const bool written = write_and_wait(request);
                client.tx_complete(written, now_ms());
                if (!written) {
                    ESP_LOGE(kTag, "Uncertain TX. Reset the ECU and hold Mode to rearm");
                }
            }
        }

        client.take_snapshot(latest);
        if (client.state() != LinkState::Live) {
            latest = {};
        }
        client.expire(latest, now_ms());
        xQueueOverwrite(telemetry_queue, &latest);
        vTaskDelay(std::max<TickType_t>(1, pdMS_TO_TICKS(2)));
    }
}

} // namespace

esp_err_t start_uart()
{
    telemetry_queue = xQueueCreate(1, sizeof(Snapshot));
    ESP_RETURN_ON_FALSE(telemetry_queue, ESP_ERR_NO_MEM, kTag, "Telemetry queue allocation failed");

    esp_err_t err = ESP_ERR_NO_MEM;
    if (SemaphoreHandle_t complete = xSemaphoreCreateBinary()) {
        UartStartup startup{complete};
        if (xTaskCreatePinnedToCore(run_uart, "cluster_uart", 5 * 1024, &startup, 5, &uart_task,
                                    xPortGetCoreID()) == pdPASS) {
            xSemaphoreTake(complete, portMAX_DELAY);
            err = startup.result;
        }
        vSemaphoreDelete(complete);
    }
    if (err != ESP_OK) {
        uart_task = nullptr;
        vQueueDelete(telemetry_queue);
        telemetry_queue = nullptr;
    }
    return err;
}

void confirm_ecu_reset()
{
    if (uart_task) {
        xTaskNotifyGive(uart_task);
    }
}

bool take_uart_snapshot(Snapshot& snapshot)
{
    return telemetry_queue && xQueueReceive(telemetry_queue, &snapshot, 0) == pdTRUE;
}

} // namespace cluster::platform
