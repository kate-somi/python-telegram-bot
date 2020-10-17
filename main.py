import requests
import re
import telebot
from telebot import types
from bs4 import BeautifulSoup as bs

bot = telebot.TeleBot("1044154144:AAE0-8IXAM5IxXc9-ps-HwqvuJtAtkMNH9Q")


def thesaurus(word):
    result = {}
    # Проверяю, есть ли слово в WordsApi, и вытаскиваю возможные опции.
    # Check WordsApi for possible queries
    queries = ["definition", "synonyms", "antonyms", "examples"]
    url = "https://wordsapiv1.p.rapidapi.com/words/" + word
    headers = {
        "x-rapidapi-host": "wordsapiv1.p.rapidapi.com",
        "x-rapidapi-key": "6d04d531bcmsh1bc2212e6676bb7p1925f7jsn72eaeaee8160"
    }
    response = requests.get(url, headers=headers)
    if response.ok:
        for query in queries:
            if query in response.text:
                result[query] = queries.index(query)
    else:
        return False
    # Проверяю, есть ли слово в Yandex.Dictionary. Если да, добавляю опцию "перевод".
    # Check Yandex.Dictionary for translation into Russian
    url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup?"
    params = {
        "key": "dict.1.1.20201014T141243Z.933988eaadec7fdd.77705db619f9ce6077c71998e204d71e80de440c",
        "lang": "en-ru",
        "text": word
    }
    response = requests.get(url, params=params).json()
    if response["def"]:
        result["translation"] = 4
    return result


def get_data_wordsapi(word, query="definitions"):
    data = []
    url = "https://wordsapiv1.p.rapidapi.com/words/" + word + "/" + query
    headers = {
        "x-rapidapi-host": "wordsapiv1.p.rapidapi.com",
        "x-rapidapi-key": "6d04d531bcmsh1bc2212e6676bb7p1925f7jsn72eaeaee8160"
    }
    raw_data = requests.get(url, headers=headers).json()
    if query == "definitions":
        for elem in raw_data["definitions"]:
            data.append(elem["definition"])
    elif query in ["synonyms", "antonyms", "examples"]:
        for elem in raw_data[query]:
            data.append(elem)
    return data


def get_data_yandex_dict(word):
    data = []
    url = "https://dictionary.yandex.net/api/v1/dicservice/lookup?"
    params = {
        "key": "dict.1.1.20201014T141243Z.933988eaadec7fdd.77705db619f9ce6077c71998e204d71e80de440c",
        "lang": "en-ru",
        "text": word
    }
    response = requests.get(url, params=params)
    raw_data = bs(response.text, features='xml')
    for elem in raw_data.find_all("tr"):
        if elem.parent.name != "ex":
            data.append(elem.find("text").get_text())
            for syn in elem.find_all("syn"):
                data.append(syn.get_text())
    return data


@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.chat.id, "Привет! Я тезаурус английского языка.\n"
                                      "Пришли мне слово или словосочетание на английском языке, "
                                      "и я посмотрю, что у меня для тебя есть.\n"
                                      "Используй команду /info, чтобы узнать больше о моем функционале.\n")
    bot.send_photo(message.chat.id, "https://ibb.co/J751v8X")


@bot.message_handler(commands=["info"])
@bot.message_handler(content_types=["audio", "document", "photo", "sticker", "video", "video_note", "voice",
                                    "location", "contact", "migrate_to_chat_id", "migrate_from_chat_id",
                                    "pinned_message"])
def cmd_info(message):
    bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAIllV-KQcyT6BJKBOEbNWCHJ3xyGN61AAJDAANEDc8XIqysVRZ-nWEbBA")
    bot.send_message(message.chat.id, "Я могу найти определение, перевод, синонимы, "
                                      "антонимы и примеры употребления слова.\n"
                                      "Иногда мои источники меня подводят, так что я сначала покажу, что из этого "
                                      "удалось найти по твоему запросу.\n"
                                      "Дай мне английское слово, а затем просто кликни нужную кнопку.")


@bot.message_handler(content_types=["text"])
def is_word(message):
    text = message.text.strip().lower()
    result = thesaurus(text)
    if result:
        # Создаю кнопки для взаимодействия с пользователем.
        # Create UI buttons
        markup_inline = types.InlineKeyboardMarkup()
        for elem in result.keys():
            # В аттрибут callback_data складываю всю нужную информацию по запросу, чтобы не хранить её в БД.
            # Use the callback_data attribute to store original queries
            markup_inline.add(types.InlineKeyboardButton(text=elem, callback_data=text + "+" + elem + "+" +
                                                         "+".join(list(map(str, (result.values()))))))
        bot.send_message(message.chat.id, u'\u2728' + text.upper(), reply_markup=markup_inline)
    elif re.match(r".*[А-ЯЁа-яё]+.*", text):
        bot.send_message(message.chat.id, "I don't understand! Speak English!")
        bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAIliV-KEy6xSFsGelIabY4E5a1PW_CmAAIJAAP3F4Er_po8d3GPgREbBA")
    else:
        bot.send_message(message.chat.id, "Увы, я не всеведущ. А точно нет опечаток?\n"
                                          "Я жду слово или словосочетание на английском языке.")
        bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAIlTl-Jr1bMsj3EyFhwiS_LFlclR7CmAAIkAAPBnGAMSCRauiUNKI4bBA")


@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    data = call.data.split("+")
    word = data[0]
    # Дублирую кнопки для взаимодействия с пользователем.
    # Re-create UI buttons
    markup_inline = types.InlineKeyboardMarkup()
    for elem in data[2:]:
        if elem == "0":
            elem = "definition"
        elif elem == "1":
            elem = "synonyms"
        elif elem == "2":
            elem = "antonyms"
        elif elem == "3":
            elem = "examples"
        else:
            elem = "translation"
        # В аттрибут callback_data складываю всю нужную информацию по запросу, чтобы не хранить её в БД.
        # Use the callback_data attribute to store original queries
        markup_inline.add(types.InlineKeyboardButton(text=elem, callback_data=word + "+" + elem + "+" +
                                                     "+".join(data[2:])))
    if data[1] == "definition":
        result = get_data_wordsapi(word=word)
        message_text = "\n".join([u'\U0001f538' + " " + i for i in result])
        bot.send_message(call.message.chat.id, "*" + word.upper() + ": definition\n*" +
                         message_text, parse_mode="Markdown", reply_markup=markup_inline)
    elif data[1] in ["synonyms", "antonyms", "examples"]:
        result = get_data_wordsapi(word=word, query=data[1])
        if data[1] == "synonyms":
            message_text = "\n".join([u'\U0001f539' + " " + i for i in result])
        elif data[1] == "antonyms":
            message_text = "\n".join([u'\U0001f53a' + " " + i for i in result])
        else:
            message_text = "\n".join([u'\U0001f538' + " " + i for i in result])
        bot.send_message(call.message.chat.id, "*" + word.upper() + ": " + data[1] + "\n*" +
                         message_text, parse_mode="Markdown", reply_markup=markup_inline)
    elif data[1] == "translation":
        result = get_data_yandex_dict(word)
        message_text = "\n".join([u'\U0001f539' + " " + i for i in result])
        bot.send_message(call.message.chat.id, "*" + word.upper() + ": translation\n*" +
                         message_text, parse_mode="Markdown", reply_markup=markup_inline)


if __name__ == '__main__':
    bot.infinity_polling()
