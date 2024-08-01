import network
from umqtt.simple import MQTTClient
import ujson
import time


class MQTT():
    def __init__(self, wifi_name, wifi_password, BROKER_IP):
        self.wifi_name = wifi_name
        self.wifi_password = wifi_password
        self.BROKER_IP = BROKER_IP
        self.sending_successful = True

# Function to connect to WLAN
    def connect(self):
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(self.wifi_name, self.wifi_password)
            count = 1
            while wlan.isconnected() == False and count <= 2:
                count += 1
                time.sleep(0.005)
                print("connecting...")
        except:
            print("Could not connect to MQTT. Pico IP")

    def connect_mqtt(self):
        mqtt_client=MQTTClient("", self.BROKER_IP)
        mqtt_client.connect(clean_session=True)
        return mqtt_client

    def publish_data(self, data):
        self.sending_successful = True
        try:
            self.connect()
            mqtt_client = self.connect_mqtt()
            i = 0
            while i < 2 :
                # Sending a message every 3 seconds.
                topic = "HRV-analysis"
                message = data
                json_message = ujson.dumps(message)
                mqtt_client.publish(topic, json_message)
                print(f"Sending to MQTT: {topic} -> {json_message}")
                time.sleep(0.5)
                i += 1

        except Exception as e:
            print(f"Failed to send MQTT message: {e}")
            self.sending_successful = False

