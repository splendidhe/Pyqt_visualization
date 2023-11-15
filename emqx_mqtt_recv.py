# python3.6
import random
import cv2
import json
import base64
import numpy as np
from paho.mqtt import client as mqtt_client


broker = '124.223.201.77'
port = 1883
topic = "mqtt/image"
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{str(len(msg.payload.decode()))}` from `{msg.topic}` topic")
        # print(msg.payload.decode())
        parsed_data = json.loads(msg.payload.decode())
        image_value = parsed_data.get("image")
        # 将base64编码的数据解码为二进制数据
        decoded_data = base64.b64decode(image_value)
        # 将二进制数据解码为图像
        image = cv2.imdecode(np.frombuffer(decoded_data, np.uint8), cv2.IMREAD_COLOR)
        cv2.imshow("Decoded Image", image)
        cv2.waitKey(1)

    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
