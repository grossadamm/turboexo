# UART boundary regression harness

`guard_race.cpp` compiles the actual `main/uart.cpp` and portable protocol against
small deterministic UART/FreeRTOS fakes. It exercises the worker loop, including
startup drain, hardware FIFO bytes below the RX interrupt threshold, an ISR
handoff into the software ring, receive FSM/line sampling order, extra bytes at
a response guard boundary, receive errors, successful publication and uncertain
TX inhibition. CTest runs it with ASan/UBSan on supported host compilers.

The fakes model specific ordering cases; they do not emulate ESP32 hardware,
measure ISR latency or establish actual FreeRTOS scheduling. The four target
builds verify the pinned SDK register/API layouts. Electrical and live timing
acceptance still requires the documented bench procedure.
