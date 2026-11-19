#pragma once
#include "cluster/types.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <deque>
#include <string>
#include <vector>

using esp_err_t = int;
constexpr int ESP_OK = 0;
constexpr int ESP_FAIL = -1;
constexpr int ESP_ERR_NO_MEM = -2;
#define ESP_RETURN_ON_ERROR(expression, tag, ...)                              \
  do {                                                                         \
    (void)(tag);                                                               \
    if (auto e = (expression); e != ESP_OK)                                    \
      return e;                                                                \
  } while (0)
#define ESP_RETURN_ON_FALSE(expression, code, tag, ...)                        \
  do {                                                                         \
    (void)(tag);                                                               \
    if (!(expression))                                                         \
      return (code);                                                           \
  } while (0)
#define ESP_LOGE(tag, ...) (void)(tag)
#define CONFIG_CLUSTER_EGO_DELAY_MS 15000
#define CONFIG_CLUSTER_LIVE 1
using gpio_num_t = int;
enum {
  GPIO_NUM_15 = 15,
  GPIO_NUM_16,
  GPIO_NUM_17,
  GPIO_NUM_18,
  GPIO_NUM_19,
  GPIO_NUM_20,
  GPIO_NUM_21,
  GPIO_NUM_39 = 39,
  GPIO_NUM_40,
  GPIO_NUM_41,
  GPIO_NUM_42,
  GPIO_NUM_43,
  GPIO_NUM_44,
  GPIO_NUM_45,
  GPIO_NUM_46
};
constexpr bool GPIO_IS_VALID_OUTPUT_GPIO(int) { return true; }
using uart_port_t = int;
enum {
  UART_NUM_1 = 1,
  UART_DATA_8_BITS,
  UART_PARITY_DISABLE,
  UART_STOP_BITS_1,
  UART_HW_FLOWCTRL_DISABLE,
  UART_SCLK_DEFAULT,
  UART_PIN_NO_CHANGE
};
enum {
  UART_DATA,
  UART_FIFO_OVF,
  UART_BUFFER_FULL,
  UART_BREAK,
  UART_PARITY_ERR,
  UART_FRAME_ERR
};
enum {
  UART_INTR_RXFIFO_OVF = 1,
  UART_INTR_BRK_DET = 2,
  UART_INTR_PARITY_ERR = 4,
  UART_INTR_FRAM_ERR = 8
};
struct uart_config_t {
  int baud_rate, data_bits, parity, stop_bits, flow_ctrl, source_clk;
};
struct uart_event_t {
  int type;
};
struct ObservableRxLevel {
  unsigned value = 1;
  unsigned (*on_read)() = nullptr;
  operator unsigned() const { return on_read ? on_read() : value; }
};
struct uart_dev_t {
  struct {
    unsigned st_urx_out = 0;
  } fsm_status;
  struct {
    ObservableRxLevel rxd;
  } status;
} fake_uart;
#define UART_LL_GET_HW(port) (&fake_uart)

using QueueHandle_t = void *;
using SemaphoreHandle_t = void *;
using TaskHandle_t = void *;
using TickType_t = unsigned;
constexpr int pdTRUE = 1;
constexpr int pdPASS = 1;
constexpr unsigned portMAX_DELAY = 100;
constexpr unsigned pdMS_TO_TICKS(unsigned ms) { return ms; }

int event_queue_storage, snapshot_queue_storage;
using cluster::Snapshot;
Snapshot snapshot;
unsigned publications = 0;
std::deque<uart_event_t> events;
std::vector<uint8_t> ring;
std::vector<uint8_t> fifo;
std::vector<std::string> tx;
unsigned pending_error = 0;
bool migrate_during_fifo_read = false;
bool reset_received = true;
bool full_tx = true;
uint64_t clock_ms = 0;
inline uint64_t esp_timer_get_time() { return clock_ms * 1000; }
inline void migrate_rx() {
  ring.insert(ring.end(), fifo.begin(), fifo.end());
  fifo.clear();
  events.push_back({UART_DATA});
}
inline unsigned uart_ll_get_rxfifo_len(uart_dev_t *) {
  if (migrate_during_fifo_read) {
    migrate_during_fifo_read = false;
    migrate_rx();
  }
  return fifo.size();
}
inline unsigned uart_ll_get_intsts_mask(uart_dev_t *) { return pending_error; }
inline unsigned uxQueueMessagesWaiting(QueueHandle_t queue) {
  assert(queue == &event_queue_storage);
  return events.size();
}
inline int uart_get_buffered_data_len(uart_port_t, size_t *n) {
  *n = ring.size();
  return ESP_OK;
}
inline int uart_read_bytes(uart_port_t, uint8_t *out, size_t n, int) {
  size_t count = std::min(n, ring.size());
  std::copy_n(ring.begin(), count, out);
  ring.erase(ring.begin(), ring.begin() + static_cast<ptrdiff_t>(count));
  return count;
}
inline int uart_tx_chars(uart_port_t, const char *data, size_t n) {
  tx.emplace_back(data, n);
  return full_tx ? n : n - 1;
}
inline int uart_wait_tx_done(uart_port_t, int) { return ESP_OK; }
inline int uart_driver_install(uart_port_t, int, int, int, QueueHandle_t *q,
                               int) {
  *q = &event_queue_storage;
  return ESP_OK;
}
inline int uart_param_config(uart_port_t, uart_config_t *) { return ESP_OK; }
inline int uart_set_pin(uart_port_t, int, int, int, int) { return ESP_OK; }
inline int uart_set_rx_timeout(uart_port_t, int) { return ESP_OK; }
inline int uart_enable_intr_mask(uart_port_t, unsigned m) {
  assert(m == UART_INTR_FRAM_ERR);
  return ESP_OK;
}
inline void uart_driver_delete(uart_port_t) {}
inline void uart_flush_input(uart_port_t) {
  ring.clear();
  fifo.clear();
}
inline int xQueueReceive(QueueHandle_t queue, void *out, int) {
  if (queue == &event_queue_storage && !events.empty()) {
    *static_cast<uart_event_t *>(out) = events.front();
    events.pop_front();
    return pdTRUE;
  }
  return 0;
}
inline void xQueueOverwrite(QueueHandle_t, const Snapshot *latest) {
  snapshot = *latest;
  if (latest->link == cluster::LinkState::Live)
    ++publications;
}
inline QueueHandle_t xQueueCreate(int, size_t) {
  return &snapshot_queue_storage;
}
inline void vQueueDelete(QueueHandle_t) {}
inline SemaphoreHandle_t xSemaphoreCreateBinary() {
  return &snapshot_queue_storage;
}
inline void xSemaphoreGive(SemaphoreHandle_t) {}
inline int xSemaphoreTake(SemaphoreHandle_t, unsigned) { return 1; }
inline void vSemaphoreDelete(SemaphoreHandle_t) {}
inline void vTaskDelete(TaskHandle_t) {}
inline int xTaskCreatePinnedToCore(void (*)(void *), const char *, int, void *,
                                   int, TaskHandle_t *, int) {
  return 0;
}
inline int xPortGetCoreID() { return 0; }
inline void xTaskNotifyGive(TaskHandle_t) {}
inline unsigned ulTaskNotifyTake(int, int) {
  if (!reset_received)
    return 0;
  reset_received = false;
  return 1;
}
void vTaskDelay(TickType_t);
