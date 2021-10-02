import ast
import os

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import requests

chat_id = 0
name = ""
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# send the state of the shadow
def message_r(payload, responseStatus, token):
    url = 'http://localhost:8080/info'
    data_send = ast.literal_eval(payload)
    print(data_send)
    data = {"chat_id": chat_id,
            "parking": name,
            "stalli": data_send["state"]["reported"]["s"]}
    requests.post(url, json=data)


# function that initialize the client mqtt with the handler function and certificates
def start2(n, id):  # n is the Thing's name and id is the chat_id that want the shadow
    global chat_id
    global name
    chat_id = id
    name = n
    myShadowClient = AWSIoTMQTTShadowClient(name)
    awshost = "a3cytfxnue36h3-ats.iot.us-west-2.amazonaws.com"
    awsport = 8883
    caPath = os.path.join(BASE_DIR, "telegramBot/certificates", "AmazonRootCA1.pem")
    certPath = os.path.join(BASE_DIR, "progetto_py/certificates/" + name + '/',  "Thing-certificate.pem.crt")
    keyPath = os.path.join(BASE_DIR, "progetto_py/certificates/" + name + '/',  "Private-private.pem.key")
    myShadowClient.configureEndpoint(awshost, awsport)
    myShadowClient.configureCredentials(caPath, keyPath, certPath)
    myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
    myShadowClient.connect()
    myDeviceShadow = myShadowClient.createShadowHandlerWithName(name, True)
    myDeviceShadow.shadowGet(message_r, 5)

