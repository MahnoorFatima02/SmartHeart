import micropython
micropython.alloc_emergency_exception_buf(200)
import ujson
import utime
from machine import Pin, PWM, I2C
import time
from fifo import Fifo
from ssd1306 import SSD1306_I2C
from oop1 import Encoder, Oled


class History:
    def __init__(self, rotary, oled):
        self.rot = rotary
        self.oled = oled
        self.path = "/history.json"
        self.measurement = {}
        self.data = {}#this will store the data loaded from json file
        self.position = 1
        self.change_rotate = 0
        self.change_button = None

    def load_data(self):
        with open(self.path, 'r') as file:
            self.data = ujson.load(file)
  
    #this function re-writes the content of json file
    def dump_data(self):
        with open(self.path, 'w') as file:
            ujson.dump(self.data,file)

    #this function show the initial display when going in the history tab
    def initial_display(self):
        self.oled.oled.fill(0)
        self.load_data()
        self.oled.oled.text("HISTORY", 35, 0, 1)
        for a in range(28, 96, 1):
            self.oled.oled.pixel(a, 9, 1)
        if len(self.data) == 0:
            self.oled.oled.text("NO DATA", 35, 20, 1)
            self.oled.oled.text("AVAILABLE", 27, 30, 1)
        for a in range(len(self.data)):
            self.oled.oled.text(f"Measurement {a+1}", 8, 12+8*a, 1)
        self.oled.oled.text("EXIT", 47, 56, 1)
        self.oled.oled.show()


    def add_measurement(self, measurement, time):
        self.measurement = measurement
        self.load_data()
        timestamp = f"{time[2]:02d}-{time[1]:02d}-{time[0]} {time[3]:02d}:{time[4]:02d}"
        self.measurement["timestamp"]=timestamp
        if len(self.data) < 5:
            for a in range(len(self.data),0,-1):
                self.data[f"measure{(a+1)}"]=self.data.pop(f"measure{a}")
            self.data["measure1"]=self.measurement
        else:
            del self.data["measure5"]
            for a in range(len(self.data),0,-1):
                self.data[f"measure{(a+1)}"]=self.data.pop(f"measure{a}")
            self.data["measure1"]=self.measurement
        self.dump_data()
    

    def update(self):
        while self.rot.fifo2.has_data():
            self.change_rotate = self.rot.fifo2.get()
            self.position += self.change_rotate
            if self.position < 1:
                self.position = 1
            elif self.position > len(self.data)+1:
                self.position = len(self.data)+1
        self.update_brackets()

    def update2(self):
        while self.rot.fifo1.has_data():
            self.change_button = self.rot.fifo1.get()
            if self.change_button == 0:
                break
    
     def main(self):
        self.position = 1
        while True:
            self.initial_display()
            while True:
                self.change_button = None
                self.update()
                self.update2()
                if self.change_button == 0:
                    break
            if self.position <= len(self.data):
                self.show_hrv()
            elif self.position > len(self.data):
                return
            while True:
                self.change_button = None
                self.update2()
                if self.change_button == 0:
                    break
    
    #this function update the brackets according to the rotary knob scroll
    def update_brackets(self):
        if self.position <= len(self.data):
            self.oled.oled.fill_rect(0, 8, 8, 8*6, 0)
            self.oled.oled.fill_rect(8*14, 8, 8, 8*6, 0)
        self.oled.oled.fill_rect(0, 56, 46, 8, 0)
        self.oled.oled.fill_rect(80, 56, 46, 8, 0)
        self.oled.oled.text("[", 0, 4+self.position*8, 1)
        self.oled.oled.text("]", 8*14, 4+self.position*8, 1)
        self.oled.oled.show()
    elif self.position > len(self.data):
        self.oled.oled.fill_rect(0, 8, 8, 8*6, 0)
        self.oled.oled.fill_rect(8*14, 8, 8, 8*6, 0)
        self.oled.oled.text("[", 39, 56, 1)
        self.oled.oled.text("]", 79, 56, 1)
        self.oled.oled.show()

    def show_hrv(self):
        self.oled.oled.fill(0)
        hrv_data = self.data[f"measure{self.position}"]
        self.oled.oled.text(f"{hrv_data["timestamp"]}", 0, 0, 1)
        self.oled.oled.text(f"MEAN HR: {hrv_data["Mean_HR"]}", 0, 8, 1)
        self.oled.oled.text(f"MEAN PPI: {hrv_data["Mean_RR"]}", 0, 16, 1)
        self.oled.oled.text(f"RMSSD: {hrv_data["RMSSD"]}", 0, 24, 1)
        self.oled.oled.text(f"SDNN: {hrv_data["SDNN"]}", 0, 32, 1)
        self.oled.oled.text(f"SNS: {hrv_data["SNS"]}", 0, 40, 1)
        self.oled.oled.text(f"PNS: {hrv_data["PNS"]}", 0, 48, 1)
        self.oled.oled.text("Press to go back", 0, 56, 1)
        self.oled.oled.show()

