#include "uart.cpp"
#include <functional>
#include <iostream>

struct TestComplete {};
struct Step {
  uint64_t ms;
  unsigned expected_writes;
  unsigned expected_publications;
  std::function<void()> before;
};
std::vector<Step> steps;
size_t step_index;

void vTaskDelay(TickType_t) {
  const auto &current = steps[step_index];
  assert(tx.size() == current.expected_writes);
  assert(publications == current.expected_publications);
  if (++step_index == steps.size())
    throw TestComplete{};
  const auto &next = steps[step_index];
  clock_ms = next.ms;
  if (next.before)
    next.before();
}
void ring_identity() {
  const std::string identity = "Speeduino 2025.01";
  ring.assign(identity.begin(), identity.end());
}
void frame(size_t size) {
  ring.assign(size, 0);
  ring[0] = 'r';
  ring[1] = 0x30;
}
void run(std::vector<Step> sequence) {
  fake_uart = {};
  snapshot = {};
  tx.clear();
  ring.clear();
  fifo.clear();
  events.clear();
  publications = 0;
  pending_error = 0;
  migrate_during_fifo_read = false;
  reset_received = true;
  full_tx = true;
  steps = std::move(sequence);
  step_index = 0;
  clock_ms = steps[0].ms;
  if (steps[0].before)
    steps[0].before();
  cluster::platform::UartStartup startup{nullptr};
  try {
    cluster::platform::run_uart(&startup);
  } catch (const TestComplete &) {
    return;
  }
  assert(false);
}
int main() {
  // The start bit precedes tick's clock sample, but the FSM has not yet
  // recognized it. Preemption lets RXD rise while the receiver becomes busy.
  // RXD -> FSM ordering catches this; the former FSM -> RXD ordering did not.
  run({
      {0, 0, 0, {}},
      {12, 0, 0,
       [] {
         fake_uart.status.rxd.on_read = [] {
           fake_uart.fsm_status.st_urx_out = 4;
           return 1u;
         };
       }},
  });
  run({
      {0, 0, 0, {}},
      {12, 0, 0, [] { fifo.push_back(0); }},
      {14, 0, 0, migrate_rx},
      {25, 0, 0, {}},
      {26, 1, 0, {}},
      {27, 1, 0, ring_identity},
      {39, 1, 0,
       [] {
         fifo.push_back('!');
         migrate_during_fifo_read = true;
       }},
      {41, 1, 0, {}},
      {53, 1, 0, {}},
  });
  assert(tx[0] == "S");
  run({
      {0, 0, 0, {}},
      {12, 1, 0, {}},
      {14, 1, 0, ring_identity},
      {26, 2, 0, {}},
      {28, 2, 0, [] { frame(46); }},
      {40, 2, 0, [] { fake_uart.fsm_status.st_urx_out = 4; }},
      {42, 3, 0, [] { fake_uart.fsm_status.st_urx_out = 0; }},
      {44, 3, 0, [] { frame(35); }},
      {56, 3, 0, [] { fifo.push_back('!'); }},
      {58, 3, 0, migrate_rx},
  });
  assert(tx[1] == std::string("r\0\x30\0\0\x2c\0", 7));
  assert(tx[2] == std::string("r\0\x30\x4c\0\x21\0", 7));
  run({
      {0, 0, 0, {}},
      {12, 1, 0, {}},
      {14, 1, 0, ring_identity},
      {26, 2, 0, {}},
      {28, 2, 0, [] { frame(46); }},
      {40, 3, 0, {}},
      {42, 3, 0, [] { frame(35); }},
      {54, 3, 0, [] { pending_error = UART_INTR_FRAM_ERR; }},
      {56, 3, 0,
       [] {
         pending_error = 0;
         events.push_back({UART_FRAME_ERR});
       }},
      {68, 3, 0, {}},
  });
  run({
      {0, 0, 0, {}},
      {12, 1, 0, {}},
      {14, 1, 0, ring_identity},
      {26, 2, 0, {}},
      {28, 2, 0, [] { frame(46); }},
      {40, 3, 0, {}},
      {42, 3, 0, [] { frame(35); }},
      {54, 3, 1, {}},
  });
  run({
      {0, 0, 0, {}},
      {12, 1, 0, [] { full_tx = false; }},
      {514, 1, 0, {}},
  });
  assert(snapshot.link == cluster::LinkState::TransportFault);
  std::cout << "PASS: UART adapter FIFO, ISR migration, FSM, pending error, "
               "quiet publication and uncertain TX\n";
}
