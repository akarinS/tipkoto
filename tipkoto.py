#!/usr/bin/env python3

from kotodrpc import KotodRpc
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.api import API
from decimal import Decimal
import sqlite3
import re
import string
import random

rpc_user = ""
rpc_password = ""
koto = KotodRpc(rpc_user, rpc_password)

database = sqlite3.connect("tipkoto.db")
db = database.cursor()
db.execute("create table if not exists data (user_id text, address text)")
database.commit()
database.close()

consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = API(auth)

def insert_data(user_id):
    database = sqlite3.connect("tipkoto.db")
    db = database.cursor()

    address = koto.call("getnewaddress")
    db.execute("insert into data (user_id, address) values (?, ?)", (user_id, address))

    database.commit()
    database.close()

    return address

def user_exists(user_id):
    database = sqlite3.connect("tipkoto.db")
    db = database.cursor()

    if len([row for row in db.execute("select * from data where user_id = ?", (user_id,))]) == 0:
        exists = False

    else:
        exists = True

    database.close()

    return exists

def get_address_of(user_id):
    database = sqlite3.connect("tipkoto.db")
    db = database.cursor()

    address = db.execute("select address from data where user_id = ?", (user_id,)).fetchone()[0]

    database.close()

    return address

def amount_is_ok(balance, amount, change):
    amount_limit = Decimal("5.4e-7")

    if balance < amount_limit:
        return False

    elif amount < amount_limit:
        return False

    elif change == 0:
        return True

    elif change < amount_limit:
        return False

    else:
        return True

def get_params(from_address, to_address, balance, amount, change):
    if change == 0:
        params = (from_address,
                  [{"address": to_address, "amount": float(amount)}])

    else:
        params = (from_address,
                  [{"address": to_address, "amount": float(amount)},
                   {"address": from_address, "amount": float(change)}])

    return params

def get_balance_of(user_id):
    address = get_address_of(user_id)
    balance = Decimal(str(koto.call("z_getbalance", address)))
    confirming_balance = Decimal(str(koto.call("z_getbalance", address, 0))) - balance

    return (balance, confirming_balance)

def address_is_ok(address):
    if address.startswith("k1") or address.startswith("jz"):
        if len(address) == 35:
            return True

    else:
        return False

def is_amount(element):
    if element == "all":
        return True

    try:
        float(element)

    except ValueError:
        return False

    return True

def on_tweet(status):
    if status.text.find("RT") == -1 and status.text.find("RT") == -1 and status.user.screen_name != "tipkototest":
        if status.text.find("@tipkototest") == -1:
            return

        name = status.user.name
        screen_name = status.user.screen_name
        user_id = "twitter-" + str(status.user.id)
        command = status.text[(status.text.find("@tipkototest") + 13):]

        if re.search("help", command) or re.search("ヘルプ", command):
            tweet = "@" + screen_name + " 使い方はこちらです！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

        elif user_exists(user_id):
            if re.search("balance", command) or re.search("残高", command):
                balance, confirming_balance = get_balance_of(user_id)

                if confirming_balance == 0:
                    tweet = "@" + screen_name + " " + name + "さんの残高は {0:f}KOTO です！".format(balance)

                else:
                    tweet = "@" + screen_name + " " + name + "さんの残高は {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming) です！".format(confirming_balance)

            elif re.search("deposit", command) or re.search("入金", command):
                address = get_address_of(user_id)
                tweet = "@" + screen_name + " このアドレスに送金してね！ " + address

            elif re.match("withdraw", command) or re.match("出金", command):
                command_elements = command.split(" ")

                if len(command_elements) < 3:
                    return

                else:
                    if address_is_ok(command_elements[2]):
                        if is_amount(command_elements[1]):
                            balance, _ = get_balance_of(user_id)

                            if command_elements[1] == "all":
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal("{0:.8f}".format(float(command_elements[1])))

                            change = balance - amount - Decimal("0.0001")

                            if amount_is_ok(balance, amount, change):
                                from_address = get_address_of(user_id)
                                to_address = command_elements[2]

                                params = get_params(from_address, to_address, balance, amount, change)
                                koto.call("z_sendmany", *params)

                                tweet = "@" + screen_name + " {0:f}KOTO を ".format(amount) + to_address + " に出金しました！"

                            else:
                                tweet = "@" + screen_name + " この額では出金できません・・・"

                        else:
                            tweet = "@" + screen_name + " 数字と認識できませんでした・・・ ちゃんと半角数字になってるか確認してみて！"

                    else:
                        tweet = "@" + screen_name + " このアドレスには出金できません・・・"

            elif re.match("tip", command) or re.match("投げ銭", command) or re.match("投銭", command):
                command_elements = command.split(" ")

                if len(command_elements) < 3 or not command_elements[2].startswith("@"):
                    return

                else:
                    to_screen_name = command_elements[2][1:]

                    try:
                        to_user = api.get_user(to_screen_name)

                    except:
                        tweet = "@" + screen_name + " 宛先（@%s）が見つかりませんでした・・・" % (to_screen_name)
                        tweet = tweet + "\n\n" + ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
                        api.update_status(status = tweet, in_reply_to_status_id = status.id)
                        return

                    to_name = to_user.name
                    to_user_id = "twitter-" + str(to_user.id)

                    if user_exists(to_user_id):
                        if is_amount(command_elements[1]):
                            balance, _ = get_balance_of(user_id)

                            if command_elements[1] == "all":
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal("{0:.8f}".format(float(command_elements[1])))

                            change = balance - amount - Decimal("0.0001")

                            if amount_is_ok(balance, amount, change):
                                from_address = get_address_of(user_id)
                                to_address = get_address_of(to_user_id)

                                params = get_params(from_address, to_address, balance, amount, change)
                                koto.call("z_sendmany", *params)

                                tweet = "@" + screen_name + " @" + to_screen_name + " " + name + "さんから" + to_name + "さんへ {0:f}KOTO の投げ銭です！".format(amount)

                            else:
                                tweet = "@" + screen_name + " この額では投げ銭できません・・・"

                        else:
                            tweet = "@" + screen_name + " 数字と認識できませんでした・・・　ちゃんと半角数字になってるか確認してみて！"

                    else:
                        tweet = "@" + screen_name + " %s（@%s）" % (to_name, to_screen_name) + "さんはこのTipBotをまだ使ってないみたい・・・"

            elif re.search("Hello", command) or re.search("Hi", command) or re.search("こんにちは", command):
                tweet = "@" + screen_name + " こんにちは！"

            elif re.search("はじめまして", command):
                tweet = "@" + screen_name + " もう！ はじめましてじゃないでしょ！"

            else:
                return

        elif re.search("Hello", command) or re.search("Hi", command) or re.search("こんにちは", command) or re.search("はじめまして", command):
            address = insert_data(user_id)
            tweet = "@" + screen_name + " はじめまして！ " + name + "さんのアドレスを用意しました！ " +  address

        else:
            return

        tweet = tweet + "\n\n" + ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
        api.update_status(status = tweet, in_reply_to_status_id = status.id)

class Listener(StreamListener):
    def on_connect(self):
        print("on_connect")

        return

    def on_status(self, status):
        print("on_status : ")
        print(status.text)
        on_tweet(status)

        return True

# on_dataは自分がオーバーライドしたらうまく動かへんからほっとく。他のがFalseを返さんかったら問題ないはず。

    def on_exception(self, exception):
        print("on_exception : ", exception)

        return

    def on_limit(self, track):
        print("on_limit : ", track)

        return

    def on_error(self, status_code):
        print("on_error : ", status_code)

        return True

    def on_timeout(self):
        print("on_timeout")

        return True

    def on_disconnect(self, notice):
        print("on_disconnect : ", notice)

        return

    def on_warning(self, notice):
        print("on_warning : ", notice)

        return

if __name__ == "__main__":
    while True:
        try:
            stream = Stream(auth, Listener(), secure = True)
            stream.userstream()

        except KeyboardInterrupt:
            break

        except:
            pass

