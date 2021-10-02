import ast

import paho.mqtt.client as paho
import os
import socket
import ssl
import requests

import gestoreNotifiche

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
subscribe = ""

flag = False
message = {}


# on the connection subscribe to the main topic
def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc))
    client.subscribe('#', 1)


# quando arriva un messaggio al topic vengono svolte determinate azioni su quel messaggio
def on_message(client, userdata, msg):
    global flag
    global message
    url = 'http://localhost:8081/notifiche'
    dict_msg = msg.payload.decode("UTF-8")
    data_send = ast.literal_eval(dict_msg)
    # se il messaggio è il cambio di stato della Thing si tiene in memoria
    if "previous" not in data_send and "metadata" not in data_send and not flag:
        flag = True
        message = data_send
    # quando arriva il messaggio che mostra lo stato precedente si verifica se ci sono casi in cui uno stallo si è liberato
    if "previous" in data_send and flag and message["state"]["reported"]["p"] == \
            data_send["previous"]["state"]["reported"]["p"]:
        flag = False
        cont = 0
        previous = data_send["previous"]["state"]["reported"]["s"]
        parking_name = message["state"]["reported"]["p"]
        for stallo in message["state"]["reported"]["s"]:
            if previous[cont]["id"] == stallo["id"] and stallo["v"] == 1 and previous[cont]["v"] == 0:
                data = {
                    "parking": parking_name,
                    "id": stallo["id"],
                    "value": stallo["v"],
                }
                requests.post(url, json=data)
            cont = cont + 1


# function that initialize the client mqtt with the handler function and certificates
def start():
    mqttc = paho.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    # mqttc.on_log = on_log
    awshost = "a3cytfxnue36h3-ats.iot.us-west-2.amazonaws.com"
    awsport = 8883
    caPath = os.path.join(BASE_DIR, "telegramBot", "certificates/AmazonRootCA1.pem")
    certPath = os.path.join(BASE_DIR, "telegramBot", "certificates/Thing-certificate.pem.crt")
    keyPath = os.path.join(BASE_DIR, "telegramBot", "certificates/Private-private.pem.key")

    mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED,
                  tls_version=ssl.PROTOCOL_TLSv1_2,
                  ciphers=None)
    mqttc.connect(awshost, awsport, keepalive=60)

    mqttc.loop_start()
    return mqttc
