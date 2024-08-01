import urequests as requests
import ujson
import network
from time import sleep
import ubinascii
from machine import UART, Pin, I2C, Timer, ADC
from ssd1306 import SSD1306_I2C
from oled import oled 

class Kubios:
    def __init__(self, wifi_name, wifi_password,oled):
        self.APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
        self.CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
        self.CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef"
        self.LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
        self.TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
        self.REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"
        self.data = 'grant_type=client_credentials&client_id={}'.format(self.CLIENT_ID)
        self.headers = {'Content-Type':'application/x-www-form-urlencoded'}
        self.wifi_name = wifi_name
        self.wifi_password = wifi_password
        self.final_result = {}
        self.oled = oled
        self.current_time = 0



    def connect(self):
        try:
            self.oled.oled.text("Connecting to", 0, 5, 1)
            self.oled.oled.text("wifi", 10, 15, 1)
            self.oled.oled.show()
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(self.wifi_name, self.wifi_password)
            count = 1
            while wlan.isconnected() == False and count < 2:
                wlan.active(True)
                wlan.connect(self.wifi_name, self.wifi_password)
                time.sleep(1)
                count += 1

        except:
            self.oled.oled.fill(0)
            self.oled.oled.text("Could not connect", 0, 5, 1)
            self.oled.oled.text(" to wifi", 30, 15, 1)
            self.oled.oled.show()

    def get_result(self):
        return self.final_result

    def show_data(self, record):
        try:
            self.oled.oled.fill(0)
            self.oled.oled.text("Sending data...", 0, 5, 1)
            self.oled.oled.show()
            dataset = {
                "type": "RRI",
                "data": record,
                "analysis": {"type": "readiness"}
            }
            response = requests.post(
                url = self.TOKEN_URL,
                data = 'grant_type=client_credentials&client_id={}'.format(self.CLIENT_ID),
                headers = {'Content-Type':'application/x-www-form-urlencoded'},
                auth = (self.CLIENT_ID, self.CLIENT_SECRET))

            response = response.json()
            access_token = response["access_token"]

            response = requests.post(
                url = "https://analysis.kubioscloud.com/v2/analytics/analyze",
                headers = { "Authorization": "Bearer {}".format(access_token),"X-Api-Key": self.APIKEY},
                json = dataset
            )
            response = response.json()
            print(response)
            self.current_time = response['analysis']['create_timestamp']
            print(self.current_time)
            date_part, time_part = (self.current_time).split('T')
            print("1")
            year, month, day = date_part.split('-')
            print("2")
            hour, minute = time_part.split(':')[0:2]
            print("3")
            timestamp_list = [int(day), int(month),int(year), int(hour), int(minute)]
            print("4")
            print(timestamp_list)
            timestamp_list[3] += 3
            print(timestamp_list)
            self.current_time = timestamp_list

            self.final_result['Mean_HR']= round(response['analysis']["mean_hr_bpm"])
            self.final_result['Mean_RR']= round(response['analysis']["mean_rr_ms"])
            self.final_result['RMSSD']= round(response['analysis']["rmssd_ms"], 2)
            self.final_result['SDNN']= round(response['analysis']["sdnn_ms"], 2)
            self.final_result['SNS']= round(response['analysis']["sns_index"], 2)
            self.final_result['PNS']= round(response['analysis']["pns_index"], 2)

            self.oled.oled.fill(0)
            self.oled.oled.text("Mean_HR", 0, 0, 1)
            self.oled.oled.text("Mean_RR", 0, 8, 1)
            self.oled.oled.text("RMSSD", 0, 16, 1)
            self.oled.oled.text("SDNN", 0, 24, 1)
            self.oled.oled.text("SNS", 0, 32, 1)
            self.oled.oled.text("PNS", 0, 40, 1)
            self.oled.oled.text("PRESS TO GO BACK", 0, 48, 1)

            self.oled.oled.text(str(self.final_result['Mean_HR']), 60, 0, 1)
            self.oled.oled.text(str(self.final_result['Mean_RR']), 60, 8, 1)
            self.oled.oled.text(str(self.final_result['RMSSD']), 60, 16, 1)
            self.oled.oled.text(str(self.final_result['SDNN']), 60, 24, 1)
            self.oled.oled.text(str(self.final_result['SNS']), 60, 32, 1)
            self.oled.oled.text(str(self.final_result['PNS']), 60, 40, 1)
            self.oled.oled.show()
            return True

        except:
            self.oled.oled.fill(0)
            self.oled.oled.text("ERROR SENDING", 0,0, 1)
            self.oled.oled.text("DATA", 32, 10, 1)
            self.oled.oled.text("PRESS BUTTON TO", 0, 25, 1)
            self.oled.oled.text("RETRY", 32, 35, 1)
            self.oled.oled.text("OR WAIT 3 SECONDS TO", 0, 45, 1)
            self.oled.oled.text("GO TO MAIN MENU", 0, 55, 1)
            self.oled.oled.show()
            return False
