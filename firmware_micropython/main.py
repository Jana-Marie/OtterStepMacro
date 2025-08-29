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

class webcom(object):
    """docstring for webcom"""
    def __init__(self, ssid, password, led_ok, led_act, trig):
        super(webcom, self).__init__()
        self.ssid = ssid
        self.password = password
        self.lok = led_ok
        self.lac = led_act

        #self.handler = handler(led_ok, led_act, trig)

        self.index = open('index.html')
        self.reply = self.index.read()

        self.stage = macroStage(trig, led_ok, led_act)

        self.lp1 = lp("WebCom")
        self.lp1.print("init done")

        self.lp2 = lp("Handler")
        self.lp2.print("init done")
        
        self.lp3 = lp("HandlerCommand")
        self.lp3.print("init done")
    
    def connect(self):
        self.lp1.print("connecting to " + self.ssid)
        
        network.WLAN(network.AP_IF).active(False)
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(self.ssid, self.password)
        
        while not self.wlan.isconnected():
            self.lac.value(self.lac.value()^1)
            time.sleep(0.33)
        self.lac.value(0)

        self.lp1.print("connected to " + self.ssid)
        self.lp1.print("IP: " + self.wlan.ifconfig()[0])

    def start_server(self):
        self.lp1.print("starting server on port 80")
        addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
        self.srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(addr)
        self.srv.listen(5)
        self.srv.setblocking(False)
        self.srv.setsockopt(socket.SOL_SOCKET, 20, self.cln_handler)
        self.lp1.print("server running on port 80")
    
    def req_handler(self, cs):
        self.lac.value(1)
        req = b''
        try:
            req = cs.read()
            if req:
                cs.write(self.reply)
            else:
                self.lp2.print("connection closed")
        except Exception as e:
            self.lp2.print("ERROR " + str(e))
        cs.close()

        if 'GET /?' in req.decode("utf-8"):
            #clist = [line for line in req.decode("utf-8").split('\n') if 'GET /?' in line][0][:-1].replace('?', '&').split('&')
            clist = [line for line in req.decode("utf-8").split('\n') if 'GET /?' in line][0].split(' ')[1][2:].split('&')

            if len(clist) > 0:
                self.lp2.print("parsing config")
                cdict = {}
                for s in clist:
                    c,a = s.split('=')
                    cdict[c] = a
                if cdict["cmd"] == "stop":
                    self.lp3.print("stop")
                    self.stage.stop()
                elif cdict["cmd"] == "home":
                    self.lp3.print("home")
                    self.stage.home()
                elif cdict["cmd"] == "run":
                    self.lp3.print("run macro stage with parameters " + cdict['start'] + " " + cdict['steps'] + " " + cdict['dps'] + " " + cdict['delay'] + " " + cdict['speed'])
                    self.lp3.print("send camera request to " + cdict['req'])
                    # start, steps, dps, delay, spd, req
                    start = int(cdict['start'])
                    steps = int(cdict['steps'])
                    dps = int(cdict['dps'])
                    delay = float(cdict['delay'])
                    speed = int(cdict['speed'])
                    req = cdict['req']
                    self.stage.run(start, steps, dps, delay, speed, req)
                elif cdict["cmd"] == "moveTo":
                    self.lp3.print("move to position ", cdict['pos'])
                    self.stage.moveTo(int(cdict['pos']))
                elif cdict["cmd"] == "moveRel":
                    self.lp3.print("move relative by ", cdict['pos'])
                    self.stage.moveRel(int(cdict['pos']))
                elif cdict["cmd"] == "setSpeed":
                    self.lp3.print("set speed to ", cdict['speed'])
                    self.stage.setSpeed(int(cdict['speed']))
                elif cdict["cmd"] == "triggerCamera":
                    self.lp3.print("camera trigger request sent to ", cdict['req'])
                    self.stage.doReq(cdict['req'], True)
                else:
                    self.lp3.print("no command found")

        self.lac.value(0)
    
    def cln_handler(self, srv):
        self.lac.value(1)
        cs,ca = self.srv.accept()
        self.lp1.print("serving " + str(ca))
        cs.setblocking(False)
        cs.setsockopt(socket.SOL_SOCKET, 20, self.req_handler(cs)) #self.handler.handle(self.handler, cs))
        self.lac.value(0)

class lp(object):
    """simple printer class"""
    def __init__(self, prefix):
        super(lp, self).__init__()
        self.p = "[" + prefix + "]"

    def print(self, txt, end='\n'):
        print(self.p, txt, end=end)
        

class macroStage(object):
    """docstring for macroStage"""
    def __init__(self, trigger, led_ok, led_act):
        super(macroStage, self).__init__()
        # Stepper Interface
        STP_STEP_PIN = 10
        STP_DIR_PIN = 1
        STP_EN_PIN = 0
        STP_PER_REV = 28570 # motor settings * gear ratio * linear slope
                            # 3200           * 3.6        * 2.48
        self.stp = Stepper(STP_STEP_PIN, STP_DIR_PIN, STP_EN_PIN, steps_per_rev=STP_PER_REV, speed_sps=500, invert_enable=True, timer_id=0)
        self.trg = trigger
        self.lok = led_ok
        self.lac = led_act

        self.lp0 = lp("MacroStage")
        self.lp0.print("init done")

    def run(self, start, steps, dps, delay, spd, req):
        self.lp0.print("running macro scheme")
        self.home()
        self.lp0.print("setting up socket")
        addr = socket.getaddrinfo(req, 8081)[0][-1]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lp0.print("moving to start pos")
        self.stp.speed(4000)
        self.moveTo(start, True)
        time.sleep(0.5)
        self.stp.speed(spd)
        self.lp0.print("start stack")
        while steps:
            self.lp0.print(str(steps) + ' steps to go')
            steps = steps - 1
            self.doReq(addr, sock)
            self.moveRel(dps, True)
            time.sleep(delay)
        self.lp0.print("macro scheme done")

    def blockRun(self):
        while not self.stp.is_target_reached():
            pass
        return

    def doReq(self, req, createSocket=False):
        self.lac.value(1)
        if createSocket:
            addr = socket.getaddrinfo(req, 8081)[0][-1]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.lp0.print("trying to trigger camera")
            sock.connect(addr)
        except Exception as e:
            self.lp0.print("trigger excited with " + str(e))

        try:
            sock.close()
        except Exception as e:
            self.lp0.print("could not close connection with " + str(e))
        self.lac.value(0)
        return

    def stop(self):
        self.stp.stop()
        return

    def setSpeed(self, speed):
        self.stp.speed(speed)
        return

    def moveRel(self, target, blocking=False):
        pos = self.stp.get_pos()
        self.stp.target(pos + target)
        if blocking:
            self.blockRun()
        return

    def moveTo(self, pos, blocking=False):
        self.stp.target(pos)
        if blocking:
            self.blockRun()
        return

    def home(self):
        self.lp0.print("homing", '\r')
        # run backwards into homing switch
        self.stp.speed(4000)
        self.stp.free_run(1)
        while not self.trg.value():
            pass
        self.stp.stop()
        # slowly go out of switch, deleting backlash
        self.lp0.print("homing ...", '\r')
        self.stp.speed(600)
        self.stp.free_run(-1)
        while self.trg.value():
            pass
        self.stp.stop()
        self.stp.overwrite_pos(0)
        self.stp.target(0)
        self.stp.track_target()
        self.lp0.print("homing successful")
        return 

if __name__ == '__main__':
    # main
    wc = webcom(SSID, PASSWORD, LED_OK, LED_ACT, TRIG)
    wc.connect()
    wc.start_server()

    LED_OK.value(1)

    while True:
        pass