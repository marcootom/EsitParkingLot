from pathlib import Path

import requests
from bottle import Bottle
from bottle import (
    response, request as bottle_request
)

from connect import *
from connect_single_park import *
from gestoreNotifiche import *

client = MongoClient('localhost:27017')
db = client['parkinglots']
col = db['users']
col_park = db['parking']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BotHandlerMixin:
    BOT_URL = None

    def get_chat_id(self, data):
        """
        Method to extract chat id from telegram request.
        """
        chat_id = data['message']['chat']['id']

        return chat_id

    def get_message(self, data):
        """
        Method to extract message id from telegram request.
        """
        message_text = data['message']['text']

        return message_text

    def send_message(self, prepared_data):
        """
        Prepared data should be json which includes at least `chat_id` and `text`
        """
        message_url = self.BOT_URL + 'sendMessage'
        requests.post(message_url, json=prepared_data)

    # message at the start of conversation
    def start_conv(self):
        return "Benvenuto/a! Questo bot ti permetterà di controllare lo stato degli stalli di un determinato parcheggio," \
               "e poter ricevere una notifica quando si libererà uno stallo di un parcheggio di tuo interesse"

    # add the parking in the list of the user
    def add_park_action(self, chat_id, message):
        result = col_park.find({"_id": message})
        answer = "L'operazione non è andata a buon fine"
        self.mod_command(chat_id, "None")
        toadd = []
        if len(list(result)) == 1:
            if not os.path.exists(BASE_DIR + '\\progetto_py\\static\\' + message + '.txt'):
                myfile = Path(BASE_DIR + '\\progetto_py\\static\\' + message + '.txt')
                myfile.touch(exist_ok=True)
            with open(BASE_DIR + '\\progetto_py\\static\\' + message + '.txt', "r+") as f:
                if str(chat_id) not in f.read():
                    toadd.append('\n' + str(chat_id))
            filePark = open(BASE_DIR + '\\progetto_py\\static\\' + message + '.txt', 'a')
            for el in toadd:
                filePark.write(el)
            if len(list(col.aggregate([{"$unwind": "$parking"}, {"$match": {"_id": chat_id, "parking": message}}]))) != 1:
                query = {"_id": chat_id}
                update = {"$addToSet": {"parking": message}}
                col.update_one(query, update)
                return "Il Parcheggio "+message+" è stato aggiunto con successo"
            else:
                return "Il Parcheggio "+message+" è già presente nella tua lista"
        else:
            return answer

    # delete the parking from the list of the user
    def delete_park_action(self, chat_id, message):
        answer = "L'operazione non è andata a buon fine, parcheggio non presente o inesistente"
        self.mod_command(chat_id, "None")
        if len(list(col.aggregate([{"$unwind": "$parking"}, {"$match": {"_id": chat_id, "parking": message}}]))) == 1:
            query = {"_id": chat_id}
            update = {"$pull": {"parking": message}}
            col.update_one(query, update)
            return "Il Parcheggio "+message+" è stato rimosso con successo"
        else:
            return answer

    # delete the data of the user from mongo db
    def delete_conv_action(self, chat_id, message):
        if message == "Y":
            query = {"_id": chat_id}
            col.delete_one(query)
            return "Tutti i dati relativi all'utente sono stati eliminati"
        elif message == "N":
            self.mod_command(chat_id, "None")
            return "La chat non è stata cancellata"
        else:
            return "Comando non valido, inserire (Y o N): "

    # start the client that take the info on the basis of the message receive
    def info_park_action(self, chat_id, message):
        result = col_park.find({"_id": message})
        self.mod_command(chat_id, "None")
        if len(list(result)) == 1:
            start2(message, chat_id)
            return "Ricerca informazioni..."
        else:
            return "Parcheggio inesistente."

    # change the state of the user
    def mod_command(self, chat_id, command):
        query = {"_id": chat_id}
        update = {"$set": {"command": command}}
        col.update_one(query, update)

    # ask on which parking the user want the notice
    def add_park_answer(self, chat_id):
        self.mod_command(chat_id, "add_park")
        lista_nomi_disponibili = "Parcheggi disponibili:\n"
        parkings_disponibili = list(col_park.find())
        for park_disp in parkings_disponibili:
            lista_nomi_disponibili = lista_nomi_disponibili + " - " + park_disp["_id"] + "\n"
        lista_nomi = "Parcheggi presenti nella tua lista:\n"
        parkings = list(col.aggregate([{"$unwind": "$parking"}, {"$match": {"_id": chat_id}}]))
        for park in parkings:
            lista_nomi = lista_nomi + " - " + park['parking'] + "\n"
        return lista_nomi_disponibili + lista_nomi+"\nScegli un parcheggio di cui vuoi ricevere le notifiche: "

    # ask on which parking the user doesn't want the notice anymore
    def delete_park_answer(self, chat_id):
        self.mod_command(chat_id, "delete_park")
        lista_nomi = "Parcheggi presenti nella tua lista:\n"
        parkings = list(col.aggregate([{"$unwind": "$parking"}, {"$match": {"_id": chat_id}}]))
        for park in parkings:
            lista_nomi = lista_nomi + " - " + park['parking'] + "\n"
        return lista_nomi+"\nScegli un parcheggio di cui vuoi ricevere le notifiche: "

    # ask on which parking the user want the info
    def info_park_answer(self, chat_id):
        self.mod_command(chat_id, "info_park")
        lista_nomi = "Parcheggi disponibili:\n"
        parkings = list(col_park.find())
        for park in parkings:
            lista_nomi = lista_nomi + " - " + park["_id"] + "\n"
        return lista_nomi+"\nScegli un parcheggio di cui vuoi conoscere lo stato attuale: "

    def chat_id_park_notify(self, parking):
        c = col.aggregate([{"$unwind": '$parking'}, {"$match": {"parking": parking}}, {"$project": {'_id': 1}}])
        return list(c)


class TelegramBot(BotHandlerMixin, Bottle):
    BOT_URL = 'https://api.telegram.org/bot1955639125:AAGuzE1r87okeNpDmX7QcyPd3zu5m415k0M/'

    def __init__(self, *args, **kwargs):
        super(TelegramBot, self).__init__()
        self.route('/', callback=self.post_handler, method="POST")
        self.route('/notifiche', callback=self.notifiche, method="POST")


    def message_default(self):
        return 'Nessun comando inserito'

    # on the basis of the command route to the right function
    def prepare_data_for_answer(self, data):
        chat_id = self.get_chat_id(data)
        user = col.find_one({"_id": chat_id})
        preview_com = "None"
        if user is None:
            user_dict = {"_id": chat_id, "command": "None", "parking": []}
            col.insert_one(user_dict)
        else:
            preview_com = user["command"]

        if preview_com == "None":
            message = self.get_message(data)
            if message == '/start':
                answer = self.start_conv()
            elif message == '/aggiungi_parcheggio':
                answer = self.add_park_answer(chat_id)
            elif message == '/elimina_parcheggio':
                answer = self.delete_park_answer(chat_id)
            elif message == '/info_parcheggio':
                answer = self.info_park_answer(chat_id)
            else:
                answer = self.message_default()
        else:
            message = self.get_message(data)
            if preview_com == 'add_park':
                answer = self.add_park_action(chat_id, message)
            elif preview_com == 'delete_park':
                answer = self.delete_park_action(chat_id, message)
            elif preview_com == 'info_park':
                answer = self.info_park_action(chat_id, message)

        json_data = {
            "chat_id": chat_id,
            "text": answer,
        }
        return json_data

    # handle all the post request except a few
    def post_handler(self):
        data = bottle_request.json
        answer_data = self.prepare_data_for_answer(data)
        self.send_message(answer_data)
        return response

        # handle the post request that bring the information of a determinate Shadow Thing
    def info(self):
        data = bottle_request.json
        stato_stalli = "Stato degli stalli:\n"
        for stallo in data['stalli']:
            if stallo["v"] == 1:
                stato_stalli = stato_stalli + " - Stallo " + str(stallo["id"]) + ": disponibile\n"
            else:
                stato_stalli = stato_stalli + " - Stallo " + str(stallo["id"]) + ": occupato\n"
        answer_data = {
            "chat_id": data["chat_id"],
            "text": "Parcheggio " + data["parking"] + "\n\n" + stato_stalli,
        }
        self.send_message(answer_data)
        return response



if __name__ == '__main__':
    start()

    app = TelegramBot()
    app.run(host='localhost', port=8080)

