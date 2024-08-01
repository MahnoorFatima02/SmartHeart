from filefifo import Filefifo
import time
from ssd1306 import SSD1306_I2C
import framebuf
from machine import UART, Pin, I2C, Timer, ADC
from led import Led
from fifo import Fifo
from piotimer import Piotimer
import micropython
import ujson
import utime
import urequests as requests
import network
import ubinascii
from umqtt.simple import MQTTClient
micropython.alloc_emergency_exception_buf(200)


class Isr_ADC:
    def __init__(self, adc_pin):
        self.adc = ADC(adc_pin)
        self.samples = Fifo(2000)
        self.adcled = Led(22)

    def handler(self, tid):
        self.adcled.toggle()
        self.samples.put(self.adc.read_u16())


class Encoder:
    def __init__(self, rot_a, rot_b, rot_push):
        self.a = Pin(rot_a, mode = Pin.IN, pull = Pin.PULL_UP)
        self.b = Pin(rot_b, mode = Pin.IN, pull = Pin.PULL_UP)
        self.p = Pin(rot_push, mode = Pin.IN, pull = Pin.PULL_UP)
        self.fifo1 = Fifo(30, typecode = 'i')
        self.fifo2 = Fifo(30, typecode = 'i')
        self.a.irq(handler = self.handler1, trigger = Pin.IRQ_RISING, hard = True)
        self.p.irq(handler = self.handler2, trigger = Pin.IRQ_FALLING, hard = True)
        self.btn_pressed_old = 0
        self.btn_pressed_new = 0
        self.led = Led(20)

    def handler1(self, pin):
        self.led.toggle()
        if self.b.value():
            self.fifo2.put(-1)
        else:
            self.fifo2.put(1)

    def handler2(self, pin):
        self.btn_pressed_new = time.ticks_ms()
        if (self.btn_pressed_new - self.btn_pressed_old) > 300:
            self.btn_pressed_old = self.btn_pressed_new
            self.fifo1.put(0)

class Oled:
    def __init__(self, width, height):
        self.i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
        self.width = width
        self.height = height
        self.oled = SSD1306_I2C(self.width, self.height, self.i2c)
        self.font_pi = 1
        self.font_cha = 8
        self.fbuf = framebuf.FrameBuffer(bytearray(2000), self.oled.width, self.oled.height, framebuf.MONO_VLSB)
        self.fbuf1 = framebuf.FrameBuffer(bytearray(2000), self.width, self.font_cha + self.font_pi, framebuf.MONO_VLSB)
        self.fbuf2 = framebuf.FrameBuffer(bytearray(2000), self.width, self.height - (self.font_cha + 2*self.font_pi), framebuf.MONO_VLSB)
        self.fbuf3 = framebuf.FrameBuffer(bytearray(2000), self.width, self.font_cha + self.font_pi, framebuf.MONO_VLSB)
        self.oled.fill(0)
        self.oled.show()

class States:
    def __init__(self, delay_time, oled, data, rotary, kubios, mqtt, history):
        self.delay = delay_time
        self.oled = oled
        self.data = data
        self.rot = rotary
        self.history = history
        self.text = ""
        self.num_option = 0
        self.change = None
        self.btn_val = False
        self.state = 0
        self.kubios = kubios
        self.mqtt = mqtt
        
    def check_btn_press(self):
        if self.rot.fifo1.has_data():
            self.change = self.rot.fifo1.get()
            if self.change == 0:
                self.btn_val ^= 1
            else:
                while self.rot.fifo1.has_data():
                    self.rot.fifo1.get()
        return self.btn_val

    def change_menu_state(self):
        if self.rot.fifo2.has_data():
            self.change = self.rot.fifo2.get()
            if self.change != 0:
                self.num_option += self.change
                if self.num_option < 0:
                    self.num_option = 0
                elif self.num_option > 4:
                    self.num_option = 4

    def clean_oled(self):
        self.oled.oled.fill(0)
        self.oled.oled.show()

    def first_menu_display(self):
        self.oled.oled.fill(0)
        self.oled.oled.text(f"_ Measure HR", 0, 0, 1)
        self.oled.oled.text(f"  Basic HRV", 0, (self.oled.font_cha + 4) * 1, 1)
        self.oled.oled.text(f"  Kubios", 0, (self.oled.font_cha + 4) * 2, 1)
        self.oled.oled.text(f"  History", 0, (self.oled.font_cha + 4) * 3, 1)
        self.oled.oled.text(f"  EXIT", 0, (self.oled.font_cha + 4) * 4, 1)
        self.oled.oled.show()
    
    def update_menu_display(self):
        self.oled.oled.fill_rect(0, 0, self.oled.font_cha * 2, self.oled.height, 0)
        self.oled.oled.text("-", 0, (self.oled.font_cha + 4) * self.num_option)
        self.oled.oled.show()
        
    def change_state_based_on_option(self):
        if self.num_option == 0:
            self.state = 3
        elif self.num_option == 1:
            self.state = 6
        elif self.num_option == 2:
            self.state = 11
        elif self.num_option == 3:
            self.state = 18
        elif self.num_option == 4:
            self.state = 19

    def state_off(self):
        self.oled.oled.fill(0)
        self.oled.oled.show()
        self.num_option = 0

    def state_begin(self):
        self.text = "Smart Heart"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(len(self.text) * self.oled.font_cha / 2), 5, 1)
        self.oled.oled.blit(self.oled.img1, 56, 30)
        self.text = "Press to start"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(len(self.text) * self.oled.font_cha / 2), self.oled.height - self.oled.font_cha, 1)
        self.oled.oled.show()
        time.sleep(0.2)
        self.oled.oled.blit(self.oled.img2, 50, 25)
        self.oled.oled.show()
        time.sleep(0.2)
        self.oled.oled.fill_rect(0, 25, self.oled.width, 30, 0)

    def state_menu(self):
        while self.rot.fifo2.has_data():
            self.change_menu_state()
        self.update_menu_display()

    #option 0: measure HR
    def state0a(self):
        self.text = "Touch the sensor"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), 5, 1)
        self.text = "and"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), self.oled.font_cha + 5*1 + self.oled.font_cha, 1)
        self.text = "Press to start"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), self.oled.font_cha * 2 + 5*2 + self.oled.font_cha, 1)
        self.oled.oled.show()

    def state0b(self):
        self.data.read()
        self.data.first_display()
        while self.data.count_display <= self.data.sample_rate * 59 and not self.check_btn_press():
            self.data.process_and_display()
        self.data.stop_read()
        self.data.count_sample = 1
        self.btn_val = False
    def state0c(self):
        self.data.display_result_state0c()

    #option 1: basic HRV
    def state1a(self):
        self.text = "Touch the sensor"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), 5, 1)
        self.text = "and"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), self.oled.font_cha + 5*1 + self.oled.font_cha, 1)
        self.text = "Press to start"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), self.oled.font_cha * 2 + 5*2 + self.oled.font_cha, 1)
        self.oled.oled.show()

    def state1b(self):
        self.data.read()
        self.data.first_display()
        while self.data.count_sample <= self.data.sample_rate * 60 and not self.check_btn_press():
            self.data.process_and_display()
        self.data.stop_read()
        self.data.count_sample = 1
        self.btn_val = False

    def state1c(self):
        self.data.display_result_state1c()

    def state1d(self):
        self.oled.oled.text("Sending...", 0, 5, 1)
        self.oled.oled.show()
        self.mqtt.publish_data(self.data.result_dictionary())
        self.clean_oled()
        if self.mqtt.sending_successful:
            self.oled.oled.text("Successful", 0, 5, 1)
            self.oled.oled.show()
        else:
            self.oled.oled.text("Failed", 0, 5, 1)
            self.oled.oled.show()
   
    def state1e(self):
        self.oled.oled.text("Bad signal", 0, 5, 1)
        self.oled.oled.text("Try again", 0, 15, 1)
        self.oled.oled.show()

    #option 2: Kubios
    def state2a(self):
        self.text = "Touch the sensor"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), 5, 1)
        self.text = "and"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), self.oled.font_cha + 5*1 + self.oled.font_cha, 1)
        self.text = "Press to start"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), self.oled.font_cha * 2 + 5*2 + self.oled.font_cha, 1)
        self.oled.oled.show()

    def state2b(self):
        self.data.read()
        self.data.first_display()
        while self.data.count_sample <= self.data.sample_rate * 60 and not self.check_btn_press():
            self.data.process_and_display()
        self.data.stop_read()
        self.data.count_sample = 1
        self.btn_val = False

    def state2c(self):
        self.kubios.connect()

    def state2d(self):
        return self.kubios.show_data(self.data.get_peaks_per_interval())

    def state2e(self):
        self.oled.oled.text("Bad signal", 0, 5, 1)
        self.oled.oled.text("Try again", 0, 15, 1)
        self.oled.oled.show()

  #option 3: History
    def state3a(self):
        self.history.main()

    #option 4: Exit
    def state4(self):
        self.text = "Thank you"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), 5, 1)
        self.text = "See you again"
        self.oled.oled.text(self.text, round(self.oled.width / 2) - round(self.oled.font_cha * len(self.text) / 2), 15, 1)
        self.oled.oled.show()