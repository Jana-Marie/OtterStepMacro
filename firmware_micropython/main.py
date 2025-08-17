from machine import Pin, I2C
from stepper import Stepper
import socket, select, time, network

SSID = ""
PASSWORD = ""

# LEDs
LED_OK = Pin(6, Pin.OUT)
LED_ACT = Pin(7, Pin.OUT)

# External IO
TRIG = Pin(8, Pin.IN, Pin.PULL_UP)

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
STP_PER_REV = 3200 # motor settings * gear ratio * linear slope
                   # 3200           * 3.6        *
stp = Stepper(STP_STEP_PIN, STP_DIR_PIN, STP_EN_PIN, steps_per_rev=STP_PER_REV, speed_sps=500, invert_enable=True, timer_id=0)

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

class macroStage(object):
    """docstring for macroStage"""
    def __init__(self, stepper, trigger, led_ok, led_act):
        super(macroStage, self).__init__()
        self.stp = stepper
        self.trg = trigger
        self.lok = led_ok
        self.lac = led_act

    def run(self, init, steps, dps, delay, spd, req):
        self.home()
        stp.speed(100)
        self.moveTo(init)
        self.blockRun()
        stp.speed(spd)
        while(steps--):
            self.doReq(req)
            self.moveRel(dps)
            self.blockRun()
            time.sleep(delay)

    def blockRun(self):
        while(stp.is_target_reached()):
            pass
        return

    def doReq(self):
        pass

    def moveRel(self, target):
        pos = stp.get_pos()
        stp.target(pos + target)
        return

    def moveTo(self, target):
        stp.target(target)
        return

    def home(self):
        # run backwards into homing switch
        stp.speed(200)
        stp.free_run(-1)
        while not self.trg.value():
            pass
        stp.stop()
        # slowly go out of switch, deleting backlash
        stp.speed(20)
        stp.free_run(1)
        while self.trg.value():
            pass
        stp.stop()
        stp.overwrite_pos(0)
        stp.target(0)
        stp.track_target()
        return True

if __name__ == '__main__':
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