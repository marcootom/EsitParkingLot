import ast
import os
import time

import AWSIoTPythonSDK
import requests
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from pymongo import MongoClient

chat_id = 0
name = ""
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client = MongoClient('localhost:27017')
db = client['parkinglots']
col_park = db['parking']
col_park_u = db['parkingUpdates']
col_users = db['users']


# send the state of the shadow
def updateMongo(payload, responseStatus, token):
    data_send = ast.literal_eval(payload)
    name = data_send["state"]["reported"]["p"]
    values = data_send["state"]["reported"]["s"]
    oldvalues = col_park_u.find_one({"_id": name})
    oldslot1 = oldvalues['slot1']
    oldslot2 = oldvalues['slot2']
    newslot1 = values[0]['v']
    newslot2 = values[1]['v']
    # Update mongo
    park = {'$set': {'slot1': newslot1, 'slot2': newslot2}}
    name_ = {"_id": name}
    col_park_u.update_one(name_, park, upsert=True)
    #Verify the changes
    if oldslot1 == 0:
        if newslot1 == 1:
            #Lo Slot si è liberato
            text = 'Lo slot 0 del parcheggio ' + name + ' si è liberato'
            with open(BASE_DIR + '\\progetto_py\\static\\' + name + '.txt', "r+") as f:
                for line in f.readlines():
                    requests.post('https://api.telegram.org/bot1955639125:AAGuzE1r87okeNpDmX7QcyPd3zu5m415k0M/sendMessage?chat_id=' + line + '&text=' + text)
    elif oldslot1 == 1:
        if newslot1 == 0:
            #Lo slot è stato occupato
            text = 'Lo slot 0 del parcheggio ' + name + ' è stato occupato'
            with open(BASE_DIR + '\\progetto_py\\static\\' + name + '.txt', "r+") as f:
                for line in f.readlines():
                    requests.post(
                        'https://api.telegram.org/bot1955639125:AAGuzE1r87okeNpDmX7QcyPd3zu5m415k0M/sendMessage?chat_id=' + line + '&text=' + text)
    # Secondo slot
    if oldslot2 == 0:
        if newslot2 == 1:
            # Lo Slot si è liberato
            text = 'Lo slot 1 del parcheggio ' + name + ' si è liberato'
            with open(BASE_DIR + '\\progetto_py\\static\\' + name + '.txt', "r+") as f:
                for line in f.readlines():
                    requests.post(
                        'https://api.telegram.org/bot1955639125:AAGuzE1r87okeNpDmX7QcyPd3zu5m415k0M/sendMessage?chat_id=' + line + '&text=' + text)
    elif oldslot2 == 1:
        if newslot2 == 0:
            # Lo slot è stato occupato
            text = 'Lo slot 1 del parcheggio ' + name + ' è stato occupato'
            with open(BASE_DIR + '\\progetto_py\\static\\' + name + '.txt', "r+") as f:
                for line in f.readlines():
                    requests.post(
                        'https://api.telegram.org/bot1955639125:AAGuzE1r87okeNpDmX7QcyPd3zu5m415k0M/sendMessage?chat_id=' + line + '&text=' + text)


# function that initialize the client mqtt with the handler function and certificates
def retrieveUpdates(n):  # n is the Thing's name and id is the chat_id that want the shadow
    global name
    name = n
    myShadowClient = AWSIoTMQTTShadowClient(name)
    MQTTClient = myShadowClient.getMQTTConnection()
    MQTTClient.configureOfflinePublishQueueing(5, AWSIoTPythonSDK.MQTTLib.DROP_OLDEST);
    awshost = "a3cytfxnue36h3-ats.iot.us-west-2.amazonaws.com"
    awsport = 443
    caPath = os.path.join(BASE_DIR, "telegramBot/certificates", "AmazonRootCA1.pem")
    certPath = os.path.join(BASE_DIR, "progetto_py/certificates/" + name + '/',  "Thing-certificate.pem.crt")
    keyPath = os.path.join(BASE_DIR, "progetto_py/certificates/" + name + '/',  "Private-private.pem.key")
    myShadowClient.configureEndpoint(awshost, awsport)
    myShadowClient.configureCredentials(caPath, keyPath, certPath)
    myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
    myShadowClient.connect()
    myDeviceShadow = myShadowClient.createShadowHandlerWithName(name, True)
    myDeviceShadow.shadowGet(updateMongo, 5)


def loop():
    while True:
        parkings_disponibili = list(col_park.find())
        for park_disp in parkings_disponibili:
            retrieveUpdates(park_disp["_id"])
            time.sleep(5)


if __name__ == '__main__':
    loop()

