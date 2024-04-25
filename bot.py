import logging
import os
import glob
import sqlite3
import requests
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, Defaults, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
BOT_TOKEN = os.environ['BOT_TOKEN']

def logger(update):
    with open("logs.txt", "a+", encoding="UTF-8") as f:
        f.write(f"[{update.effective_user.first_name} | @{update.effective_user.username} | {update.message.date.astimezone()}]   {update.message.text} \n ——————————————— \n")

def checktype(message):
    if message.text:
        return (message.text, "text")
    if message.photo:
        return (message.photo, "photo")
    if message.sticker:
        return (message.sticker, "sticker")
    if message.audio:
        return (message.audio, "audio")
    if message.voice:
        return (message.voice, "voice")
    if message.animation:
        return (message.animation, "animation")
    if message.document:
        return (message.document, "document")
    if message.video_note:
        return (message.video_note, "video_note")
    if message.video:
        return (message.video, "video")
    return None

def get_nick(update):
    nick = cur.execute(f"""SELECT nickname FROM nicknames WHERE id = {update.effective_user.id}""").fetchall()[0][0]
    return nick

def set_nick(update, nick):
    cur.execute(f"""INSERT INTO
                        nicknames (id, nickname)
                    VALUES
                        ({update.effective_user.id}, '{nick}');""")
    con.commit()

con = sqlite3.connect("data/users.db")
cur = con.cursor()

user_ids = []
rooms = {}
bot = ""
types = {"text": "",
         "photo": "",
         "audio": "",
         "sticker": "",}
help_message = """
/nickname – установить никнейм

/makeroom [имя комнаты] – создать комнату

/joinroom [имя комнаты] – войти в комнату

/leaveroom – покинуть комнату

/showrooms – показать список комнат

/help – показать список команд
            """

SET_NICKNAME = range(1) 

async def nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger(update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите никнейм")
    return SET_NICKNAME

async def set_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    nick = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Вас теперь зовут {nick}")
    set_nick(update, nick)
    return ConversationHandler.END

async def makeroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    if update.effective_user.id not in user_ids:
        user_ids.append(update.effective_user.id)
        if context.args:
            rooms[context.args[0]] = [update.effective_user.id]
        else:
            rooms[str(len(rooms) + 1)] = [update.effective_user.id]
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Чат создан типо")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ты уже создал чат дурень")
    
async def joinroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    room = str(context.args[0])
    if room not in rooms.keys():
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет такой комнаты дурачина")
    else:
        rooms[room].append(update.effective_user.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Вы присоединились к комнате")
        nick = get_nick(update)
        await context.bot.send_message(chat_id=rooms[room][0], text=f"{nick} присоединился к вашей комнате")
    
async def showrooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    names = "Доступные комнаты: \n"
    if rooms:
        for i in rooms.items():
            creator = await context.bot.get_chat(i[1][0])
            nick = cur.execute(f"""SELECT nickname FROM nicknames WHERE id = {creator.id}""").fetchall()[0][0]
            names += f"\nСоздатель: {nick} \nИмя комнаты: {i[0]} \nУчастников: {len(i[1])}"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=names)

async def leaveroom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    for i in rooms.items():
        if update.effective_user.id in i[1]:
            if update.effective_user.id in user_ids:
                user_ids.pop(user_ids.index(update.effective_user.id))
            i[1].pop(i[1].index(update.effective_user.id))
            rooms[i[0]] = i[1]
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы покинули комнату")
            if i[1]:
                nick = get_nick(update)
                await context.bot.send_message(chat_id=i[1][0], text=f"{nick} покинул комнату")
            else:
                del rooms[i[0]]
            break

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    message = checktype(update.message)
    if message:
        for room in rooms.items():
            if update.effective_user.id in room[1]:
                for idrecieve in room[1]:
                    if idrecieve != update.effective_user.id:
                        nick = get_nick(update)
                        await context.bot.send_message(chat_id=idrecieve, text=f"Сообщение от: {nick}")
                        if message[1] == "text":
                            await context.bot.send_message(chat_id=idrecieve, text=message[0])
                        elif message[1] == "audio":
                            await context.bot.send_audio(chat_id=idrecieve, audio=message[0])
                        elif message[1] == "sticker":
                            await context.bot.send_sticker(chat_id=idrecieve, sticker=message[0])
                        elif message[1] == "photo":
                            await context.bot.send_photo(chat_id=idrecieve, photo=message[0][2])
                        elif message[1] == "animation":
                            await context.bot.send_animation(chat_id=idrecieve, animation=message[0])
                        elif message[1] == "voice":
                            await context.bot.send_voice(chat_id=idrecieve, voice=message[0])
                        elif message[1] == "document":
                            await context.bot.send_document(chat_id=idrecieve, document=message[0])
                        elif message[1] == "video_note":
                            await context.bot.send_video_note(chat_id=idrecieve, video_note=message[0])
                        elif message[1] == "video":
                            await context.bot.send_video(chat_id=idrecieve, video=message[0])        
                break

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    nick = requests.request('GET', 'https://random-word-api.herokuapp.com/word').text.strip('[""]')
    set_nick(update, nick)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Напишите /help для просмотра списка команд")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger(update)
    print(user_ids, rooms)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    nick_handler = ConversationHandler(
        entry_points=[CommandHandler('nickname', nickname)],
        states={
            SET_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_nickname)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    echo_handler = MessageHandler(filters.TEXT and (~filters.COMMAND), echo)
    start_handler = CommandHandler('start', start)
    makeroom_handler = CommandHandler('makeroom', makeroom)
    joinroom_handler = CommandHandler('joinroom', joinroom)
    leaveroom_handler = CommandHandler('leaveroom', leaveroom)
    info_handler = CommandHandler('info', info)
    showrooms_handler = CommandHandler('showrooms', showrooms)
    help_handler = CommandHandler('help', help)

    application.add_handler(nick_handler)
    application.add_handler(echo_handler)
    application.add_handler(start_handler)
    application.add_handler(makeroom_handler)
    application.add_handler(joinroom_handler)
    application.add_handler(info_handler)
    application.add_handler(showrooms_handler)
    application.add_handler(help_handler)
    application.add_handler(leaveroom_handler)
    
    application.run_polling()