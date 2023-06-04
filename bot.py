import os
import re
import threading
import queue
import traceback

import schedule
import telebot
from telebot.apihelper import ApiTelegramException
from threading import Thread
from time import sleep
import requests
from telegram.constants import ParseMode
from flask import Flask, request, Response
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display
import chromedriver_autoinstaller
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import socket
import pytz
from datetime import datetime,time
import json

# ------------------------------------------------------------------------------

TOKEN = '5135184922:AAGd8aNyUT8mDj7Ltm03rDos-bymW5xX4Bg'
MAIL = 'memeoflux@gmail.com'
PSW = 'AntoDipi_22'
URL = 'https://www.facebook.com/people/Dubai-coffee-lounge/100087591040668/'
LOGURL='https://www.facebook.com/login/'

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
daily = True
new_menu = None
global driver
# sslify = SSLify(server)

# ------------------------------------------------------------------------------

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# ------------------------------------------------------------------------------


def write_id(id):

    #with open('database.txt', 'a', encoding='utf8') as file:
     #   file.write(str(id) + "\n")

     dati = {"id": id}
     try:
        with open("database.json", "r") as file:
            dati_esistenti = json.load(file)
     except FileNotFoundError:
        dati_esistenti = []

     dati_esistenti.append(dati)

     with open("database.json", "w") as file:
        json.dump(dati_esistenti, file)

def write_name(nick, name, surname):
    with open("nomi.json", "r+") as f:
        # Leggi il contenuto del file
        content = f.read()
        # Se il file è vuoto, scrivi direttamente il nuovo record
        if not content:
            user_data = {"nickname": nick, "first_name": name, "last_name": surname}
            json.dump(user_data, f)
            f.write('\n')
        else:
            # Altrimenti, cerca se esiste già un record con lo stesso nickname
            f.seek(0)  # torna all'inizio del file
            found = False
            for line in f:
                record = json.loads(line)
                if record["nickname"] == nick:
                    found = True
                    break
            # Se non esiste già un record con lo stesso nickname, aggiungi il nuovo record
            if not found:
                f.seek(0, 2)  # vai alla fine del file
                user_data = {"nickname": nick, "first_name": name, "last_name": surname}
                json.dump(user_data, f)
                f.write('\n')
                
                
def add_name(nickname, first_name, last_name):
    # Leggi il contenuto del file JSON
    with open("nomi.json", 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            # Se il file è vuoto o non ha un formato JSON valido, inizializza data come una lista vuota
            data = []

    # Verifica se l'elemento esiste già nel file
    elementi_esistenti = [elemento for elemento in data if elemento.get('nickname') == nickname]
    if elementi_esistenti:
        return

    # Crea il nuovo elemento da aggiungere
    nuovo_elemento = {
        'nickname': nickname,
        'first_name': first_name,
        'last_name': last_name
    }

    # Aggiungi il nuovo elemento alla lista dei dati
    data.append(nuovo_elemento)

    # Scrivi i dati aggiornati nel file JSON
    with open("nomi.json", 'w') as file:
        json.dump(data, file, indent=4)

def write_txt(file, text):
    f = open(file, 'w', encoding='utf8')
    f.write(text)
    f.close()


def read_ids():
    try:
        with open('database.json', 'r', encoding='utf8') as file:
            contenuto = file.read()
        dati = json.loads(contenuto)
        ids = [str(d['id']) for d in dati]
        print(ids)
    except:
        print("No dati")
        ids = []
        
    return ids


def delete_element(id_to_delete):
    
    with open('database.json', 'r', encoding='utf8') as file:
        dati = json.load(file)
    
    dati = [dato for dato in dati if str(dato['id']) != id_to_delete]
    
    with open('database.json', 'w', encoding='utf8') as file:
        json.dump(dati, file)


def send_menu(menu):
    print("Sono in send")
    sleep(5)
    database = read_ids()
    for id in database:
        if id != "":
            try:
                #bot.send_message(int(id), menu)
                message_queue.put((int(id), menu))
            except:
                print("Errore")
                
def conta_database(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        record_count = len(data)
        return record_count


def leggi_database(file_path):
    with open(file_path) as file:
        data = json.load(file)

    elementi = []
    for elemento in data:
        campo = elemento[list(elemento.keys())[0]]
        elementi.append(campo)

    return elementi


def leggi_nomi(file_path):
    with open(file_path) as file:
        data = json.load(file)

    elementi = []
    for elemento in data:
        campi = [campo for campo in elemento.values() if campo is not None]
        elementi.append(" - ".join(campi))

    risultato = "\n".join(elementi)
    return risultato           
                
# ------------------------------------------------------------------------------
def process_message_queue():
    while True:
        try:
            user_id, text = message_queue.get()
            try:
                bot.send_message(user_id, text)
            except ApiTelegramException as e:
                if e.result_json['error_code'] == 403:
                    # Bot blocked by the user
                    delete_element(str(id))
                else:
                    try:
                        bot.send_message(168648726, e.result_json)
                    except:
                        print("Errore")
            except:
                print("Errore")
                
            sleep(0.5)
            message_queue.task_done()
        except Exception as e:
            error_message = f"Queue errore: {traceback.format_exc()}"
            bot.send_message(168648726, error_message)
            try:
                message_queue.task_done()
            except:
                print("Errore queue done")
            
    bot.send_message(168648726, "Queue chiusa")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("START")
    user_id = message.chat.id
    user_nickname = message.chat.username
    user_first_name = message.chat.first_name
    user_last_name = message.chat.last_name
    
    try:
        #write_name(user_nickname,user_first_name,user_last_name)
        add_name(user_nickname,user_first_name,user_last_name)
    except:
        print("Errore scrittura nome")

    if str(user_id) in read_ids():
        #bot.send_message(user_id, 'Sei già presente nel database! Appena disponibile ti sarà inviato il menu del giorno.')
        message_queue.put((user_id, 'Sei già presente nel database! Appena disponibile ti sarà inviato il menu del giorno.'))
        sleep(1)
    else:
        write_id(user_id)
        #bot.send_message(user_id, 'Benvenuto! Sei stato inserito nel database! Appena disponibile ti sarà inviato il menu del giorno.')
        message_queue.put((user_id, 'Benvenuto! Sei stato inserito nel database! Appena disponibile ti sarà inviato il menu del giorno.'))
        sleep(1)
        helper(message)
        global new_menu, daily

        if not daily:
            #bot.send_message(user_id,new_menu)
            message_queue.put((user_id,new_menu))
            sleep(1)

@bot.message_handler(commands=['autori'])
def send_autori(message):
    print("AUTORI")
    user_id = message.chat.id
    if str(user_id) in read_ids():
        bot.send_message(user_id, text = 'Gli autori di questo bot sono:\n\nTELEGRAM:\n @antonio_adascaliti \n @lodipi \n\nINSTAGRAM:\n <a href="https://www.instagram.com/antonio_adascaliti/">antonio_adascaliti</a>  \n <a href="https://www.instagram.com/lorenzo.dipi/">lorenzo.dipi</a>', parse_mode=ParseMode.HTML)
        #message_queue.put((user_id, ('Gli autori di questo bot sono:\n\nTELEGRAM:\n @antonio_adascaliti \n @lodipi \n\nINSTAGRAM:\n <a href="https://www.instagram.com/antonio_adascaliti/">antonio_adascaliti</a>  \n <a href="https://www.instagram.com/lorenzo.dipi/">lorenzo.dipi</a>', ParseMode.HTML)))
        sleep(1)
    else:
        #bot.send_message(user_id, text = "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi")
        message_queue.put((user_id,"Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)


@bot.message_handler(commands=['stop'])
def remove_user(message):
    print("STOP")
    user_id = message.chat.id
    if str(user_id) in read_ids():
        delete_element(str(user_id))
        #bot.send_message(user_id, 'Ci dispiace che tu ci lasci così presto! Usa il comando /start per tornare!')
        message_queue.put((user_id, 'Ci dispiace che tu ci lasci così presto! Usa il comando /start per tornare!'))
        sleep(1)
    else:
        #bot.send_message(user_id, text = "Il bot è già disattivato. \nUtilizza il comando /start per avviarlo!")
        message_queue.put((user_id, "Il bot è già disattivato. \nUtilizza il comando /start per avviarlo!"))
        sleep(1)


@bot.message_handler(commands=['help'])
def helper(message):
    print("HELP")
    user_id = message.chat.id
    if str(user_id) in read_ids():
        #bot.send_message(user_id, 'In questo bot potrai utilizzare i seguenti comandi:\n - /start per inserire il tuo id nel nostro database (ci serve solo per inviarti il menu!)\n - /stop per rimuovere il tuo id dal database quando lo vorrai\n - /help per farti inviare questo messaggio\n - /autori per sapere chi ha fatto questo bot')
        message_queue.put((user_id, 'In questo bot potrai utilizzare i seguenti comandi:\n - /start per inserire il tuo id nel nostro database (ci serve solo per inviarti il menu!)\n - /stop per rimuovere il tuo id dal database quando lo vorrai\n - /help per farti inviare questo messaggio\n - /autori per sapere chi ha fatto questo bot'))
        sleep(1)
    else:
        #bot.send_message(user_id, text = "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi")
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)
        
        
@bot.message_handler(commands=['stats'])
def stats(message):
    try:
        user_id = message.chat.id
        print("STATS")
        print(user_id)
        if(str(user_id)=="220450935" or str(user_id)=="168648726"):
            num_db = conta_database("database.json")
            num_nomi = conta_database("nomi.json")
            #bot.send_message(user_id, str(num_db))
            #sleep(1)
            #bot.send_message(user_id, str(num_nomi))
            
            stringa = "database: '{}' \nnomi: '{}'".format(num_db, num_nomi)
            #bot.send_message(user_id, stringa)
            message_queue.put((user_id, stringa))
            sleep(1)
    except:
        print("Errore conteggio")

@bot.message_handler(commands=['nomi'])
def names(message):
    try:
        user_id = message.chat.id
        print("NOMI")
        print(user_id)
        if(str(user_id)=="220450935" or str(user_id)=="168648726"):
            nomi = leggi_nomi("nomi.json")
            #bot.send_message(user_id, str(nomi))
            message_queue.put((user_id, str(nomi)))
            sleep(1)
    except:
        print("Errore lettura nomi")

@bot.message_handler(commands=['database'])
def databaseID(message):
    try:
        user_id = message.chat.id
        print("DATABASE")
        print(user_id)
        if(str(user_id)=="220450935" or str(user_id)=="168648726"):
            db = leggi_database("database.json")
            #bot.send_message(user_id, str(db))
            message_queue.put((user_id, str(db)))
            sleep(1)
    except:
        print("Errore lettura database")        
# ------------------------------------------------------------------------------
def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


def format(menu):

    menu = menu.replace("Oggi vi proponiamo:","Buongiorno, oggi vi proponiamo: 🍽️")
    menu = menu.replace("PRIMI", "\nPRIMI 🍝")
    menu = menu.replace("SECONDI", "\nSECONDI 🍖")
    menu = menu.replace("CONTORNI", "\nCONTORNI 🍟🥦")
    menu = menu.replace("FRUTTA E YOGURT", "\nFRUTTA E YOGURT 🍎🍍🥛")
    menu = menu.replace("DOLCI", "\nDOLCI 🍰")

    menu = menu.replace(" -", "-")
    menu = menu.replace("\n-", "-")
    menu = menu.replace("-", "\n - ")

    menu = menu + "\n\nVI ASPETTIAMO!"

    return menu


def setup():
    global driver

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--force-dark-mode')
    chrome_options.add_argument("--start-maximized")

    capabilities = {
        "resolution": "2560X1440"
        # "resolution": "1280X720"
        #"resolution": "768X432"
    }
    #service = Service(ChromeDriverManager().install())
    service = Service('/opt/render/project/.render/chrome/opt/google/chrome/chrome')
    driver = webdriver.Chrome(options=chrome_options, desired_capabilities=capabilities, service=service)
    print('Setup selenium complete')
    return driver


def get_menu():

    global div_block
    global driver

    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    #driver.delete_all_cookies()
    #driver.get("https://www.facebook.com/people/Dubai-coffee-lounge/100087591040668/")


    try:
        #chromedriver_autoinstaller.install(cwd=True)
        #chromedriver_path = os.path.join(os.getcwd(), '112', 'chromedriver')

        #driver_path = r"112\chromedriver.exe"
        #driver = webdriver.Chrome(driver_path)
        display = Display(visible=0, size=(2000, 1500))
        display.start()

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--disable-dev-shm-usage')
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="90.0.4430.24").install()),options=chrome_options) #(version="90.0.4430.24")
        driver = webdriver.Chrome(service=Service("./chromedriver"), options=chrome_options)
        driver.delete_all_cookies()

        # driver = setup()

        print("DENTRO")

        driver.get(LOGURL)
        try:
            driver.find_element(by=By.XPATH, value = '//button[@data-testid="cookie-policy-manage-dialog-accept-button"]').click()
        except:
            print("niente cookies")

        sleep(2)
        driver.find_element(by=By.XPATH, value='//input[@name="email"]').send_keys(MAIL)
        driver.find_element(by=By.XPATH, value='//input[@name="pass"]').send_keys(PSW)
        driver.find_element(by=By.XPATH, value='//button[@name="login"]').click()


        sleep(2)

        driver.get(URL)

        sleep(5)

        while(driver.title=="Facebook"):
            sleep(2)

        f = open("sourceurl.txt", "w",  encoding="utf-8")
        f.write(driver.page_source)
        f.close()


        print("Page title was '{}'".format(driver.title))

        sleep(2)
        try:
            driver.find_element(by=By.XPATH, value='//div[@aria-label="Consenti solo i cookie essenziali"]').click()
        except:
            print("Cookies non richiesti")

        sleep(2)
        try:
            #driver.find_element(by=By.XPATH, value="//div[@aria-label='Close']").click()
            driver.find_element(by=By.XPATH, value="//div[@class='x92rtbv x10l6tqk x1tk7jg1 x1vjfegm']").click()
            sleep(2)
        except:
            print("Niente da chiudere")

        f = open("source.txt", "w",  encoding="utf-8")
        f.write(driver.page_source)
        f.close()

        sleep(2)

        div_block = None

        while div_block is None:
            try:
                div_block = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'div[data-pagelet="ProfileTimeline"]')))
            except:
                div_block = None
                sleep(2)


        print("passato il ciao")
        i = 1
        bool = True
        element = None

        while bool:
            try:
                element = WebDriverWait(div_block, 10).until(EC.visibility_of_element_located((By.XPATH, './/div[contains(text(), "Oggi vi proponiamo")]')))
                element.find_element(by=By.XPATH, value="//div[contains(text(), 'Altro...')]").click()
                sleep(1)
                element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs.x126k92a')))
                bool = False
            except:
                print("Except Menu")
                driver.execute_script("window.scrollBy(0, 10);")
                sleep(1)
        
        print(element.text)
        return format(element.text)
    finally:
        print("FINE")





def write_new_menu(menu):
    global daily
    file = open('menu.txt', 'w', encoding='utf-8')
    file.write(menu)
    file.close
    daily = False


def update():

    global new_menu, daily
    print(f"Guarda mamma sono in update! {daily} \n")
    check = True
    n = 0
    if daily:
        while check and n<20:
            n=n+1
            file = open('menu.txt', 'r', encoding="utf-8")
            old_menu = file.read()
            file.close()
            
            new_menu = get_menu()

            if new_menu!=old_menu:
                write_new_menu(new_menu)
                send_menu(new_menu)
                check = False
            else:
                driver.close()
                print("attendo 10 minuti")
                sleep(600)
        print("Guarda mamma ho chiuso il driver")
        driver.close()
    else:
        file = open('menu.txt', 'r', encoding="utf-8")
        m = file.read()
        file.close()
        send_menu(m)


def update_wrapper():
    t = threading.Thread(target=update)
    t.daemon = True
    t.start()

def daily_trigger():
    global daily
    daily = True
    
def connection_server():
        while True:
            try:
                while True:
                    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5599)))
                    sleep(300)
            except Exception as e:
                print("Connessione persa. Ripristino in corso...")
                time.sleep(5)  # Attendere per 5 secondi prima di riprovare il ripristino
                continue
                
                
def connection_bot():
        while True:
            try:
                if not bot.infinity_polling():
                    bot.infinity_polling()
            except Exception as e:
                print("Connessione bot persa. Ripristino in corso...")
                time.sleep(5)  # Attendere per 5 secondi prima di riprovare il ripristino
                continue

# ------------------------------------------------------------------------------

# Creazione della coda dei messaggi
message_queue = queue.Queue()
t5 = threading.Thread(target=process_message_queue)
t5.daemon = True
t5.start()

bot.remove_webhook()
#bot.polling()
print("Inizio")
if __name__ == "__main__":
    print("IF")
    #t = threading.Thread(target=bot.polling)

    #update_wrapper()
    #new_menu = get_menu()
    #write_new_menu(new_menu)

    print("t passato")
    TIME = "09:00"

    schedule.every().day.at("00:00", "Europe/Rome").do(daily_trigger)

    schedule.every().monday.at(TIME, "Europe/Rome").do(update_wrapper)
    schedule.every().tuesday.at(TIME, "Europe/Rome").do(update_wrapper)
    schedule.every().wednesday.at(TIME, "Europe/Rome").do(update_wrapper)
    schedule.every().thursday.at(TIME, "Europe/Rome").do(update_wrapper)
    schedule.every().friday.at(TIME, "Europe/Rome").do(update_wrapper)
    
    print("schedule passati")



    t2=Thread(target = schedule_checker)
    t2.daemon = True
    t2.start()
    print("t2 fatto")
    
    t = threading.Thread(target=connection_server)
    t.daemon = True
    t.start()
    
    t_bot = threading.Thread(target=connection_bot)
    t_bot.daemon = True
    t_bot.start()
    #server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5599)))
   

#
# ------------------------------------------------------------------------------
