from machine import Pin, I2C
from stepper import Stepper
import socket, select, time, network

SSID = ""
PASSWORD = ""

# LEDs
LED_OK = Pin(6, Pin.OUT)
LED_ACT = Pin(7, Pin.OUT)

# External IO
TRIG = Pin(8, Pin.IN)

# Buttons
BTN_L = Pin(9, Pin.IN)
BTN_R = Pin(2, Pin.IN)
BTN_OK = Pin(3, Pin.IN)

# I2C, STUSB4500 and Display are usually on the bus
I2C0_SCL = Pin(4)
I2C0_SDA = Pin(5)
I2C0_STUSB4500_ADDR = 0x28
I2C0_DISPLAY_ADDR = 0x3C

# Stepper Interface
STP_STEP_PIN = 10
STP_DIR_PIN = 1
STP_EN_PIN = 0
STP_PER_REV = 3200
stp = Stepper(STP_STEP_PIN, STP_DIR_PIN, STP_EN_PIN, steps_per_rev=STP_PER_REV, speed_sps=500, invert_enable=True, timer_id=0)

# Network
network.WLAN(network.AP_IF).active(False)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)
while not wlan.isconnected():
    LED_ACT.value(LED_ACT.value()^1)
    time.sleep(0.33)
LED_ACT.value(0)
wlan.ifconfig()

def req_handler(cs):
    LED_ACT.value(1)
    try:
       req = cs.read()
       if req:
          print('req:', req)
          rep = b'Hello\r\n'
          cs.write(rep)
       else:
          print('Client close connection')
    except Exception as e:
        print('Err:', e)
    cs.close()
    LED_ACT.value(0)

def cln_handler(srv):
    LED_ACT.value(1)
    cs,ca = srv.accept()
    print('Serving:', ca)
    cs.setblocking(False)
    cs.setsockopt(socket.SOL_SOCKET, 20, req_handler)
    LED_ACT.value(0)

port = 80
addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(addr)
srv.listen(5)
srv.setblocking(False)
srv.setsockopt(socket.SOL_SOCKET, 20, cln_handler)

# main
LED_OK.value(1)

while True:
    pass