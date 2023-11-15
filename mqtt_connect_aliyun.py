import hmac
from hashlib import sha1
import time
from paho.mqtt.client import MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING, MQTT_LOG_ERR, MQTT_LOG_DEBUG
from paho.mqtt import client as mqtt
import json
import random
import threading
import cv2
import base64

# 设备证书（ProductKey、DeviceName和DeviceSecret），三元组
productKey = 'a1YGTqzEyRl'
deviceName = 'vedio'
deviceSecret = 'af12059a54ad89fb4b31b8f3dd5aec3d'

# ClientId Username和 Password 签名模式下的设置方法，参考文档 https://help.aliyun.com/document_detail/73742.html?spm=a2c4g.11186623.6.614.c92e3d45d80aqG
# MQTT - 合成connect报文中使用的 ClientID、Username、Password
mqttClientId = deviceName + '|securemode=3,signmethod=hmacsha1|'
mqttUsername = deviceName + '&' + productKey
content = 'clientId' + deviceName + 'deviceName' + deviceName + 'productKey' + productKey
mqttPassword = hmac.new(deviceSecret.encode(), content.encode(), sha1).hexdigest()

# 接入的服务器地址
regionId = 'cn-shanghai'
# MQTT 接入点域名
brokerUrl = productKey + '.iot-as-mqtt.' + regionId + '.aliyuncs.com'
# Topic，post，客户端向服务器上报消息
topic_post = '/sys/' + productKey + '/' + deviceName + '/thing/event/property/post'
# Topic，set，服务器向客户端下发消息
topic_set = '/sys/' + productKey + '/' + deviceName + '/thing/service/property/set'
# 物模型名称的前缀（去除后缀的数字）
modelName = 'image'

# 下发的设置报文示例：{"method":"thing.event.property.post","params":{"image":"1234567890"}}
# json合成上报开关状态的报文
def json_switch_set(data):
    switch_info = {}
    switch_data = json.loads(json.dumps(switch_info))
    switch_data['method'] = '/thing/event/property/post'
    switch_data['id'] = random.randint(100000000,999999999) # 随机数即可，用于让服务器区分开报文
    switch_status = {modelName : data}
    switch_data['params'] = switch_status
    return json.dumps(switch_data, ensure_ascii=False)


# 建立mqtt连接对象
client = mqtt.Client(mqttClientId, protocol=mqtt.MQTTv311, clean_session=True)
# 日志打印函数
def on_log(client, userdata, level, buf): 
    if level == MQTT_LOG_INFO:
        head = 'INFO'
    elif level == MQTT_LOG_NOTICE:
        head = 'NOTICE'
    elif level == MQTT_LOG_WARNING:
        head = 'WARN'
    elif level == MQTT_LOG_ERR:
        head = 'ERR'
    elif level == MQTT_LOG_DEBUG:
        head = 'DEBUG'
    else:
        head = level
    # print('%s: %s' % (head, buf))
# MQTT成功连接到服务器的回调处理函数
def on_connect(client, userdata, flags, rc):
    # print('Connected with result code ' + str(rc))
    # 与MQTT服务器连接成功，之后订阅主题
    # client.subscribe(topic_post, qos=0)
    client.subscribe(topic_set, qos=0)
    # 向服务器发布测试消息
    # client.publish(topic_post, payload='test msg', qos=0)
# MQTT接收到服务器消息的回调处理函数
def on_message(client, userdata, msg):
    # print('recv:', msg.topic + ' ' + str(len(msg.payload)))
    pass
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected disconnection %s' % rc)

def mqtt_connect_aliyun_iot_platform():
    client.on_log = on_log
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.username_pw_set(mqttUsername, mqttPassword)
    print('clientId:', mqttClientId)
    print('userName:', mqttUsername)
    print('password:', mqttPassword)
    print('brokerUrl:', brokerUrl)
    # ssl设置，并且port=8883
    # client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
    try:
        client.connect(brokerUrl, 1883, 60)
    except:
        print('阿里云物联网平台MQTT服务器连接错误,请检查设备证书三元组、及接入点的域名！')
    client.loop_forever()

def publish_loop():
    while 1:
        time.sleep(5)
        switchPost = json_switch_set('22222')
        client.publish(topic_post, payload=switchPost, qos=0)

def encode_loop():
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    # 初始化计数器和计时器
    frame_count = 0
    start_time = time.time()
    while True:
        # 读取摄像头画面
        ret, frame = cap.read()
        if not ret:
            break
        # 缩放画面大小为240*320  800 * 600
        resized = cv2.resize(frame, (200, 150), interpolation=cv2.INTER_AREA)
        # cv2.imshow('Origin', frame)
        # 压缩参数
        quality = 80  # 设置压缩质量，范围是1-100，值越高质量越好，文件大小越大
        # 将画面编码为jpg格式
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, quality])
        # 使用base64编码
        encoded = base64.b64encode(buffer).decode('utf-8')
        # print(encoded)
        # 计算编码后字符串的长度
        # print("压缩后：" + str(len(encoded)))
        # 显示图像
        cv2.imshow('Camera', resized)
        # 发布消息
        switchPost = json_switch_set(encoded)
        client.publish(topic_post, payload=switchPost, qos=0)
        # 帧计数器自增
        frame_count += 1
        # 按q键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        # 当计数到达一定数量时进行帧率计算
        if frame_count % 30 == 0:
            end_time = time.time()
            elapsed_time = end_time - start_time
            start_time = end_time
            fps = frame_count / elapsed_time
            print("传输帧率: {:.2f} fps".format(fps) + "  压缩后：" + str(len(encoded)))

    # 释放摄像头资源
    cap.release()
    cv2.destroyAllWindows()
    

if __name__ == '__main__':
    # 建立线程t1：mqtt连接阿里云物联网平台
    # 建立线程t2：定时向阿里云发布消息：5s为间隔，变化开关状态
    task1 = threading.Thread(target=mqtt_connect_aliyun_iot_platform, )
    # task2 = threading.Thread(target=publish_loop, )
    task3 = threading.Thread(target=encode_loop, )
    task1.start()
    # task2.start()
    task3.start()
    task1.join()
    # task2.join() 
    task3.join()         
