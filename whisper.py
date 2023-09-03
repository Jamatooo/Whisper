import re
import telebot
import mysql.connector
from telebot import types

mydb = mysql.connector.connect(
  host="#host",
  user="#user",
  password="#password",
  database="#database"
)

history = []

bot = telebot.TeleBot("#token")

#functions to work with database
def select_rumors(username):
    mycursor = mydb.cursor()
    sql = "SELECT whisper FROM rumors WHERE nickname='%s'"%(username)
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    return myresult

#check user_id if exists
def check_user_id(id):
    mycursor = mydb.cursor()
    sql = "SELECT user_id FROM users WHERE user_id='%d'"%(id)
    mycursor.execute(sql)

    myresult = mycursor.fetchall()
    if myresult == []:
        print("It's empty")
        return None
    else:
        return myresult[0][0]

def register_user(id):
    idcheck = check_user_id(id)
    if idcheck == None:
        if id and int(id):
            mycursor = mydb.cursor()
            sql = "INSERT INTO users (user_id) VALUE(%d)"%(id)
            mycursor.execute(sql)
            mydb.commit()
            print("user registered")
    else:
        print("You cannot register one more time")


# fucntions to handle nickname
def handle_link_username(link):
    x = re.findall("(^.+\/)(.+)(\?|\/)", link)
    return (x[0][1])

def handle_dog_username(u):
    if "@" in u:
        return (u[1:])

def handle_nickname(username):
    if "https://instagram.com" in username:
        username = handle_link_username(username)
        return username
    elif "@" in username:
        username = handle_dog_username(username)
        return username
    else:
        return username

def connect_instagram_profile(nickname,user_id):
    if user_id:
        mycursor = mydb.cursor()
        sql = "UPDATE users SET nickname='%s' WHERE user_id=%d"%(nickname,user_id)
        mycursor.execute(sql)
        mydb.commit()

#get username having id
def getusername(id,userid):
    mycursor = mydb.cursor()
    sql = "SELECT nickname FROM users WHERE user_id='%d'"%(id)
    mycursor.execute(sql)

    myresult = mycursor.fetchall()
    if myresult == []:
        print("It's empty")
        register_user(userid)
        return None
    else:
        return myresult[0][0]

def userexists(username):
    mycursor = mydb.cursor()
    sql = "SELECT nickname FROM users WHERE nickname='%s'"%(username)
    mycursor.execute(sql)

    myresult = mycursor.fetchall()
    if myresult == []:
        print("It's empty")
        return False
    else:
        return True




@bot.message_handler(commands=['start'])
def whisper(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtna = types.KeyboardButton('Leave feedback')
    itembtnb = types.KeyboardButton('About me')

    markup.row(itembtna, itembtnb)
    bot.send_message(message.chat.id,"Welcome to Whisper. Send us instagram profile username with @ or link of someone you want to read feedback about", reply_markup=markup)
    register_user(message.from_user.id)


"""
@bot.message_handler(commands=['history'])
def show_history(message):
    list_of_history = []
    
    unique_history = set(history)
    for x in unique_history:
        list_of_history.append("@"+x+"\n")
    
    s = ''.join(list_of_history)
    if len(s) == 0:
         bot.send_message(message.chat.id, "History is empty")
    else:
        bot.send_message(message.chat.id, "Your history of usernames\n\n"+s)
"""
    

@bot.message_handler(func=lambda message: True)
def handle_alltext(message):

    if message.text == "About me":
        username = getusername(message.from_user.id,message.from_user.id)
        us = userexists(username)
        if us:
            a = []
            a = select_rumors(username)
            if a != []:
                for x in a:
                    bot.send_message(message.chat.id, x)
            else:
                bot.send_message(message.chat.id, "There is no feedback about this profile")
        else:
            bot.send_message(message.chat.id, "Your instagram is not connected to bot. Send your profile link to connect")
            bot.register_next_step_handler(message, register)
    
    elif message.text == "Leave feedback":
        bot.send_message(message.chat.id, "Send me the username or link of the profile you want to live feedback about")
        bot.register_next_step_handler(message, leave_feedback)


    elif message.text != "About me" and message.text != "Leave feedback" and message.text != "/start":
        username = message.text
        username = handle_nickname(username)

        all = []
        if message.text:
            all = select_rumors(username)
            if all != []:
                for x in all:
                    bot.send_message(message.chat.id, x)
            else:
                bot.send_message(message.chat.id, "There is no feedback about this profile")

def register(message):  
    if "https://instagram.com" in message.text:
            username = handle_link_username(message.text)
            user_id = check_user_id(message.from_user.id)
            connect_instagram_profile(username, user_id)
            bot.send_message(message.chat.id, "You have been connected")
    else:
          bot.send_message(message.chat.id, "You need to enter profile link. Press 'about us' and try again")

useRname = None
def leave_feedback(message):
    global useRname
    useRname = handle_nickname(message.text)
    bot.send_message(message.chat.id, "Now send me the feedback about this profile")
    bot.register_next_step_handler(message, send_whisper)

def send_whisper(message):
    global useRname
    if message.text != [] and message.text != None and message.text != "Leave feedback" and message.text != "About me" :
        if len(useRname) > 30:
            bot.send_message(message.chat.id, "Fill out appropriate nickname")
        else:
            mycursor = mydb.cursor()
            sql = "INSERT INTO rumors (nickname,whisper) VALUES('%s','%s')"%(useRname, message.text)
            mycursor.execute(sql)
            mydb.commit()
            bot.send_message(message.chat.id, "Feedback sent")
    else:
        bot.send_message(message.chat.id, "You need to send feedback")



@bot.message_handler(content_types=['document', 'audio','photo','sticker','video','voice','location','contact'])
def handle_docs_audio(message):
	bot.send_message(message.chat.id, "Sorry only text")



bot.infinity_polling()
