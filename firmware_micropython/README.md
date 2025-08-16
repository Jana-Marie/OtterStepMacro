# flashing

To flash the OtterStepMacro you need to unplug all power sources, press and hold down the `<<` key, while plugging in the USB-Data cable into the `Data` port (see silkscreen on the back). Your OtterStepMacro should show up as a serial device on your computer, the `ACT` LED should be dimmly lit. You can now use run `esptool --chip esp32c3 --port /dev/ttyACM0 --baud 460800 write_flash -z 0x0 ESP32_GENERIC_C3-20250415-v1.25.0.bin` to flash the MicroPython binary via JTAG/USB-Serial.

## dependencies

You will need to move the ... 

`ampy -p /dev/ttyACM0 put micropython-stepper/src/stepper`
`ampy -p /dev/ttyACM0 put tinyweb-master/tinyweb`