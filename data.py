from filefifo import Filefifo
import time
from ssd1306 import SSD1306_I2C
import framebuf
from machine import UART, Pin, I2C, Timer, ADC
from led import Led
from fifo import Fifo
from piotimer import Piotimer
import micropython
import utime
import ubinascii
from umqtt.simple import MQTTClient
micropython.alloc_emergency_exception_buf(200)


class Data:
    def __init__(self, adc_pin, sample_rate, oled):
        self.adc = Isr_ADC(adc_pin)
        self.sample_rate = sample_rate
        self.oled = oled
        self.count_sample = 1
        self.sample = 0
        #variable for display
        self.x1 = 0
        self.y1 = 40
        self.x2 = 0
        self.y2 = 0
        self.count_display = 0
        self.mid_val = 65525 / 2
        #variable for processing
        self.avr = 0
        self.min_hr = 40
        self.max_hr = 110
        self.pre_peak_index = 0
        self.cur_peak_index= 0
        self.pre_peak = 0
        self.cur_peak = 0
        self.sum_sample = 0
        self.interval_num = 0
        self.ppi = 0
        self.sdnn = 0
        self.rmssd = 0
        self.sum_ppi = 0
        self.mean_ppi = 0
        self.mean_hr = 0
        self.ppi_list = []
        self.hr_dic = {}
        self.ppi_display = []

    def read(self):
        self.tmr = Piotimer(mode = Piotimer.PERIODIC, freq = self.sample_rate, callback = self.adc.handler)

    def stop_read(self):
        while self.adc.samples.has_data():
            self.adc.samples.get()
        self.tmr.deinit()

    def check_variability(self):
        return abs(int((self.cur_peak_index - self.pre_peak_index + 1) * 1000 / self.sample_rate) - self.ppi) < 120
    
    def get_avr(self):
        self.sum_sample += self.sample
        self.avr = self.sum_sample / self.count_sample

    def hr_detect(self):
        if self.sample > (self.avr * 1.1):
            if self.sample > self.cur_peak:
                self.cur_peak = self.sample
                self.cur_peak_index = self.count_sample
        else:
            if self.cur_peak > 0:
                if (self.cur_peak_index - self.pre_peak_index) > (60 * self.sample_rate / self.min_hr):
                        self.pre_peak = 0
                        self.pre_peak_index = self.cur_peak_index
                else:
                    if self.cur_peak >= (self.pre_peak * 0.8):
                        if (self.cur_peak_index - self.pre_peak_index) > (60 * self.sample_rate / self.max_hr):
                            if self.pre_peak > 0:
                                if self.ppi != 0:
                                    if self.check_variability():
                                        self.interval_num = self.cur_peak_index - self.pre_peak_index
                                        self.ppi = round(self.interval_num * 1000 / self.sample_rate)
                                        self.ppi_list.append(self.ppi)
                                        self.ppi_display.append(self.ppi)
                                        print(round(60/self.ppi*1000))
                                else:
                                    self.interval_num = self.cur_peak_index - self.pre_peak_index
                                    self.ppi = round(self.interval_num * 1000 / self.sample_rate)
                            self.pre_peak = self.cur_peak
                            self.pre_peak_index = self.cur_peak_index
            self.cur_peak = 0

    def cal_mean_ppi(self):
        self.sum_ppi = 0
        for i in self.ppi_list:
            self.sum_ppi += i
        self.mean_ppi = round(self.sum_ppi / len(self.ppi_list))
        self.hr_dic["mean_ppi"] = self.mean_ppi

    def cal_mean_hr(self):
        self.mean_hr = round(60 / self.mean_ppi * 1000)  
        self.hr_dic["mean_hr"] = self.mean_hr
        
    def cal_SDNN(self):
        self.sdnn = 0
        for i in self.ppi_list:
            self.sdnn += (i - self.mean_ppi)**2
        self.sdnn = round((self.sdnn / (len(self.ppi_list) - 1))**(1/2))
        self.hr_dic["sdnn"] = self.sdnn

    def cal_RMSSD(self):
        self.rmssd = 0
        difference = 0
        for i in range(len(self.ppi_list) - 1):
            difference = self.ppi_list[i+1] - self.ppi_list[i]
            self.rmssd += difference**2
        self.rmssd = round((self.rmssd / (len(self.ppi_list) - 1)) ** 0.5)
        self.hr_dic["rmssd"] = self.rmssd

    def get_peaks_per_interval(self):
       return self.ppi_list

    def result_dictionary(self):
        return self.hr_dic

    # methods for display
    def convert(self):
        self.mid_val = 0.8 * self.mid_val + 0.2 * self.sample
        self.y2 = round((self.mid_val-self.sample) / 350 + 25)
        if self.y2 > self.oled.height - (self.oled.font_cha + 2 * self.oled.font_pi) * 2 - 4 * self.oled.font_pi:
            self.y2 = self.oled.height - (self.oled.font_cha + 2 * self.oled.font_pi) * 2 - 4 * self.oled.font_pi
        elif self.y2 < (self.oled.font_pi * 4 ):
            self.y2 = self.oled.font_pi * 4

    def first_display(self):
        self.oled.oled.fill(0)
        self.oled.fbuf1.fill(1)
        self.oled.fbuf3.fill(1)
        self.oled.oled.blit(self.oled.fbuf1, 0, 0)
        self.oled.oled.blit(self.oled.fbuf3, 0, self.oled.height - self.oled.font_cha - 2*self.oled.font_pi)
        self.oled.oled.show()

    def update_fbuf1(self):
        if len(self.ppi_display) >= 3:
            self.sum_ppi = 0
            for i in self.ppi_display:
                self.sum_ppi += i
                mean_ppi = round(self.sum_ppi / len(self.ppi_display))
                mean_hr = round(60 / mean_ppi * 1000)
            self.text = "HR:" + str(mean_hr)
            self.oled.fbuf1.fill(1)
            self.oled.fbuf1.text(self.text, int(self.oled.width / 2 - len(self.text)* self.oled.font_cha / 2), self.oled.font_pi, 0)
            self.oled.oled.blit(self.oled.fbuf1, 0, 0)
            print(self.ppi_display)
            self.ppi_display = []
    def update_fbuf2(self):
        self.x2 = self.x1 + 1
        self.convert()
        self.oled.fbuf2.line(self.x1, self.y1, self.x2, self.y2, 1)
        self.oled.oled.blit(self.oled.fbuf2, 0, self.oled.font_cha + 2*self.oled.font_pi)
        
    def update_fbuf3(self):
        self.oled.fbuf3.fill(1)
        self.text = "Timer:" + str(round(self.count_sample / self.sample_rate)) + "s"
        self.oled.fbuf3.text(self.text, int(self.oled.width / 2 - len(self.text)* self.oled.font_cha / 2) , self.oled.font_pi, 0)
        self.oled.oled.blit(self.oled.fbuf3, 0, self.oled.height - self.oled.font_cha - 2*self.oled.font_pi)
    # main method
    def process_and_display(self):
        while self.count_sample < 200:
            if self.adc.samples.has_data():
                self.sample = self.adc.samples.get()
                self.get_avr()
                self.count_sample += 1
        if self.adc.samples.has_data():
            self.sample = self.adc.samples.get()
            self.count_sample += 1
            self.count_display += 1
            self.get_avr()
            if self.count_display % 10 == 0:
                if (self.count_sample / self.sample_rate) % 5 == 0:
                    self.update_fbuf1()               
                self.update_fbuf2()
                self.update_fbuf3()
                self.oled.oled.show()
                self.x1 = self.x2
                self.y1 = self.y2
                if self.x1 > 127:
                    self.x1 = 0
                    self.oled.fbuf2.fill(0)
                    self.oled.oled.show()
            self.hr_detect()

    def reset(self):
        self.x1 = 0
        self.y1 = 40
        self.x2 = 0
        self.y2 = 0
        self.count_display = 0 
        self.mid_val = 65525 / 2
        self.oled.fbuf1.fill(0)
        self.oled.fbuf2.fill(0)
        self.oled.fbuf3.fill(0)
        self.avr = 0
        self.min_hr = 40
        self.max_hr = 110 
        self.pre_peak_index = 0
        self.cur_peak_index= 0
        self.pre_peak = 0
        self.cur_peak = 0
        self.sum_sample = 0
        self.interval_num = 0
        self.ppi = 0
        self.sdnn = 0
        self.rmssd = 0
        self.sum_ppi = 0
        self.mean_ppi = 0
        self.mean_hr = 0
        self.ppi_list = []
        self.hr_dic = {}
        self.ppi_display = []

    def check_bad_signal(self):
        if len(self.ppi_list) <= 3:
            return True
        else:
            return False

    def display_result_state0c(self):
        if len(self.ppi_list) > 3:
            self.cal_mean_ppi()
            self.cal_mean_hr()
            self.oled.oled.text(f"Mean PPI = {self.mean_ppi}", 0, 5, 1)
            self.oled.oled.text(f"Mean HR = {self.mean_hr}", 0, 15, 1)
            self.oled.oled.text("Press to go back", 0, self.oled.height - 5 - self.oled.font_cha, 1)
            self.oled.oled.show()
        else:
            self.oled.oled.text("Bad signal", 0, 5, 1)
            self.oled.oled.text("Try again", 0, 15, 1)
            self.oled.oled.text("Press to go back", 0, self.oled.height - 5 - self.oled.font_cha, 1)
            self.oled.oled.show()
            
    def display_result_state1c(self):
        self.cal_mean_ppi()
        self.cal_mean_hr()
        self.cal_SDNN()
        self.cal_RMSSD()
        self.oled.oled.text(f"Mean PPI = {self.mean_ppi}", 0, 5, 1)
        self.oled.oled.text(f"Mean HR = {self.mean_hr}", 0, 15, 1)
        self.oled.oled.text(f"SDNN = {self.sdnn}", 0, 25, 1)
        self.oled.oled.text(f"RMSSD = {self.rmssd}", 0, 35, 1)
        self.oled.oled.text("Press to send", 0, self.oled.height - 5 - self.oled.font_cha, 1)
        self.oled.oled.show()
