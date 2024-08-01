from filefifo import Filefifo
import time
from ssd1306 import SSD1306_I2C
import framebuf
from machine import UART, Pin, I2C, Timer, ADC, RTC
from led import Led
from fifo import Fifo
from piotimer import Piotimer
import micropython
import utime
import ubinascii
from umqtt.simple import MQTTClient
from class_oop import Isr_ADC, Encoder, Oled, Data, MQTT, Kubios, History, States
micropython.alloc_emergency_exception_buf(200)
import heart, bigheart



image1 = heart.img
image2 = bigheart.img
WIFI_NAME = "KME761_Group_3"
WIFI_PASSWORD = "NhiTrungMahnoor"
BROKER_IP = "192.168.103.100"
rot = Encoder(10, 11, 12)
oled = Oled(128, 64, image1, image2)
data = Data(26, 250, oled)
mqtt = MQTT(WIFI_NAME, WIFI_PASSWORD, BROKER_IP)
kubios = Kubios(WIFI_NAME, WIFI_PASSWORD, oled)
history = History(rot, oled)



sys = States(0.05, oled, data, rot, kubios, mqtt,history)



while True:
    #off
    if sys.state == 0:
        sys.state_off()
        if sys.check_btn_press():
            sys.btn_val = False
            sys.state = 1
    #start system
    elif sys.state == 1:
        sys.state_begin()
        if sys.check_btn_press():
            sys.btn_val = False
            sys.state = 2
    #choose option
    elif sys.state == 2:
        sys.first_menu_display()
        while True:
            sys.state_menu()
            if sys.check_btn_press():
                sys.btn_val = False
                sys.clean_oled()
                sys.change_state_based_on_option()
                sys.data.reset()
                break
    #option 0: measure HR
    elif sys.state == 3:
        sys.state0a()
        if sys.check_btn_press():
            sys.clean_oled()
            sys.btn_val = False
            sys.state = 4
    elif sys.state == 4:
        sys.state0b()
        sys.state = 5
        sys.clean_oled()
    elif sys.state == 5:
        sys.state0c()
        if sys.check_btn_press():
            sys.clean_oled()
            sys.btn_val = False
            sys.state = 2
    #option 1: basic HRV
    elif sys.state == 6:
        sys.state1a()
        if sys.check_btn_press():
            sys.clean_oled()
            sys.btn_val = False
            sys.state = 7
    elif sys.state == 7:
        sys.state1b()
        if sys.data.check_bad_signal():
            sys.state = 10
        else:
            sys.state = 8
        sys.clean_oled()
    elif sys.state == 8:
        sys.state1c()
        if sys.check_btn_press():
            sys.clean_oled()
            sys.btn_val = False
            sys.state = 9
    elif sys.state == 9:
        sys.state1d()
        time.sleep(2)
        sys.state = 2
    elif sys.state == 10:
        sys.state1e()
        time.sleep(2)
        sys.state = 2    

    #option 2: Kubios
    elif sys.state == 11:
        sys.state2a()
        if sys.check_btn_press():
            sys.clean_oled()
            sys.btn_val = False
            sys.state = 12

    elif sys.state == 12:
        sys.state2b()
        if len(sys.data.ppi_list) < 15:
            sys.state = 13
        else:
            sys.state = 14
        sys.clean_oled()
    elif sys.state == 13:
        sys.state1e()
        time.sleep(2)
        sys.state = 2

    elif sys.state == 14:
        sys.state2c()
        sys.state = 15

    elif sys.state == 15:
        kubios_response = sys.state2d()
        if kubios_response:
            sys.state = 17
        else:
            sys.state = 16

    elif sys.state == 16:
        time_begin = time.ticks_ms()
        time_end = 0
        while True:
            time_end = time.ticks_ms()
            if sys.check_btn_press():
                sys.clean_oled()
                sys.btn_val = False
                sys.state = 14
                break
            if time_end - time_begin >= 5000:
                sys.state = 2
                break

    elif sys.state == 17:
        if sys.check_btn_press():
            sys.history.add_measurement(sys.kubios.final_result, sys.kubios.current_time)
            sys.clean_oled()
            sys.btn_val = False
            sys.state = 2

    #option 3: History
    elif sys.state == 18:
        sys.state3a()
        sys.clean_oled()
        sys.state = 2

    #option 4: Exit
    elif sys.state == 19:
        sys.state4()
        sys.state = 0
        time.sleep(0.5)
