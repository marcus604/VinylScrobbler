import pigpio, time, os
import keyboard
import threading

Enc_DT = 17
Enc_CLK = 18
Enc_SW = 4
DISP_BL = 21

pi = 0

last_DT = 1
last_CLK = 1
last_gpio = 0

counter = 100

def toggleBacklight():
        if pi.read(DISP_BL = 1):
                pi.write(DISP_BL, 0)
        else:
                pi.write(DISP_BL, 1)

def init():
        global pi
        counter = 100
        pi = pigpio.pi()                # init pigpio deamon
        pi.write(DISP_BL, 1)
        pi.set_mode(Enc_DT, pigpio.INPUT)
        pi.set_mode(Enc_CLK, pigpio.INPUT)
        pi.set_mode(Enc_SW, pigpio.INPUT)
        pi.callback(Enc_DT, pigpio.EITHER_EDGE, rotary_interrupt)
        pi.callback(Enc_CLK, pigpio.EITHER_EDGE, rotary_interrupt)
        pi.callback(Enc_SW, pigpio.FALLING_EDGE, rotary_switch_interrupt)
        os.system("fim -a -q data/images/*.jpg")

def rotary_switch_interrupt(gpio,level,tim):
        time.sleep(0.3)
        print("Count is: {}".format(counter))
        if(pi.read(Enc_SW) == 1):
                print("short press")
                return
        print("long press")
        keyboard.press_and_release('n')


# Callback fn:
def rotary_interrupt(gpio,level,tim):
        global last_DT, last_CLK,  last_gpio, counter

        if gpio == Enc_DT:
                last_DT = level
        else:
                last_CLK = level

        if gpio != last_gpio:                                   # debounce
                last_gpio = gpio
                if gpio == Enc_DT and level == 1:
                        if last_CLK == 1:
                                counter += 1
                                keyboard.press_and_release('n')
                                print("UP to {}".format(counter))
                elif gpio == Enc_CLK and level == 1:
                        if last_DT == 1:
                                counter -= 1
                                keyboard.press_and_release('b')
                                print("DOWN to {}".format(counter))

# init and loop forever (stop with CTRL C)
init()
while 1:
        time.sleep(10)
        toggleBacklight()
