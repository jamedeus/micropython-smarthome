# Mock Testing Environment

Goal: Run hardware-level unit tests on cpython in order to measure coverage.

This will require mocked versions of all micropython modules not included in cpython, as well as replacing modules that function differently with mocks.

# stdlib Modules
- [ ] logging
- [ ] struct.pack
- [ ] socket
- [ ] json
- [ ] os
- [ ] random
- [ ] re

# Micropython modules
- [x] machine.pin
- [x] machine.PWM
- [x] machine.SoftI2C
- [x] machine.Timer
- [ ] machine.RTC
- [ ] ir_tx.Player
- [ ] time.sleep_ms
- [x] time.sleep_us
- [x] urequests
- [x] uasyncio
- [ ] ubinascii
- [x] si7021
- [ ] gc
- [ ] network
- [ ] webrepl
- [ ] uos
- [ ] flashbdev
