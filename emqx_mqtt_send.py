# python 3.8

import random
import time
import cv2
import json
import base64
from paho.mqtt import client as mqtt_client


broker = '124.223.201.77'
port = 1883
topic = "mqtt/image"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'python_send'
password = '**********'
p_fps = 0

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def json_switch_set(fps, chunked_data):
    switch_info = {}
    switch_data = json.loads(json.dumps(switch_info))
    switch_data['id'] = '1'
    switch_data['fps'] = fps
    switch_data['image'] = chunked_data
    return json.dumps(switch_data, ensure_ascii=False)


def publish(client):
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    time.sleep(1)
    start_time = time.time()
    frame_count = 0
    while True:
        global p_fps
        # 读取摄像头画面
        ret, frame = cap.read()
        if not ret:
            break
        # 缩放画面大小为240*320  720, 480
        resized = cv2.resize(frame, (600, 400), interpolation=cv2.INTER_AREA)
        cv2.imshow('Carmera', resized)
        cv2.waitKey(1)
        # 压缩参数
        quality = 60  # 设置压缩质量，范围是1-100，值越高质量越好，文件大小越大
        # 将画面编码为jpg格式
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
        # 使用base64编码
        encoded = base64.b64encode(buffer).decode('utf-8')
        msg = json_switch_set(p_fps, encoded)
        result = client.publish(topic, msg)
        # 帧计数器自增
        frame_count += 1
        # result: [0, 1]
        status = result[0]
        if status == 0:
            # 当计数到达一定数量时进行帧率计算
            if frame_count % 30 == 0:
                end_time = time.time()
                elapsed_time = end_time - start_time
                start_time = time.time()
                p_fps = 30 / elapsed_time
                print("传输帧率: {:.2f} fps".format(p_fps))
                print(f"Send `{str(len(encoded))}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        
    # 释放摄像头资源
    cap.release()
    cv2.destroyAllWindows()


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()