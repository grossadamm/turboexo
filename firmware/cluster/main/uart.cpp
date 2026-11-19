#include "platform.hpp"

#include <algorithm>
#include <array>

#include "cluster/protocol.hpp"
#include "driver/uart.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"

namespace cluster::platform {
namespace {

constexpr char kTag[] = "cluster_uart";
constexpr uart_port_t kPort = UART_NUM_1;
constexpr int kRxBufferBytes = 512;
constexpr unsigned kEventCapacity = 32;
QueueHandle_t uart_events = nullptr;
QueueHandle_t telemetry_queue = nullptr;
TaskHandle_t uart_task = nullptr;

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

void check_receive_errors(TelemetryClient& client)
{
    uart_event_t event{};
    bool receive_error = false;
    for (unsigned n = 0; n < kEventCapacity && xQueueReceive(uart_events, &event, 0); ++n) {
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
    if (receive_error) {
        client.transport_error(now_ms());
        uart_flush_input(kPort);
    }
}

// Bound the work per pass. Defer the client's quiet timer and UART writes
// while earlier bytes remain in the driver's receive buffer.
bool drain_receive(TelemetryClient& client)
{
    std::array<uint8_t, kRxBufferBytes> rx{};
    const int received = uart_read_bytes(kPort, rx.data(), rx.size(), 0);
    size_t pending = 0;
    if (received < 0 || uart_get_buffered_data_len(kPort, &pending) != ESP_OK) {
        client.transport_error(now_ms());
        return false;
    }
    if (received > 0) {
        client.receive(rx.data(), static_cast<size_t>(received), now_ms());
    }
    return pending == 0;
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

void run_uart(void*)
{
    TelemetryClient client(client_config());
    Snapshot latest{};
    while (true) {
        if (ulTaskNotifyTake(pdTRUE, 0) != 0) {
            client.confirm_ecu_reset(now_ms());
        }
        check_receive_errors(client);
        if (drain_receive(client)) {
            check_receive_errors(client);
            const TxRequest request = client.tick(now_ms());
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
    return uart_set_rx_timeout(kPort, 2);
}

} // namespace

esp_err_t start_uart()
{
    telemetry_queue = xQueueCreate(1, sizeof(Snapshot));
    ESP_RETURN_ON_FALSE(telemetry_queue, ESP_ERR_NO_MEM, kTag, "Telemetry queue allocation failed");

    esp_err_t err = uart_driver_install(kPort, kRxBufferBytes, 0, kEventCapacity, &uart_events, 0);
    if (err == ESP_OK) {
        err = configure_uart();
        if (err == ESP_OK && xTaskCreate(run_uart, "cluster_uart", 5 * 1024, nullptr, 5, &uart_task) != pdPASS) {
            err = ESP_ERR_NO_MEM;
        }
        if (err != ESP_OK) {
            uart_driver_delete(kPort);
        }
    }
    if (err != ESP_OK) {
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
