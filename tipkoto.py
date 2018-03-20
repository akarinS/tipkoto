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
import logging
import logging.config

rpc_user = ""
rpc_password = ""
koto = KotodRpc(rpc_user, rpc_password)

database = sqlite3.connect("tipkoto.db")
db = database.cursor()
db.execute("create table if not exists users (user_id text, address text)")
database.commit()
database.close()

consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = API(auth)

logging.config.fileConfig("logging.conf")
logger = logging.getLogger()

def insert_data(user_id):
    database = sqlite3.connect("tipkoto.db")
    db = database.cursor()

    address = koto.call("getnewaddress")
    db.execute("insert into users (user_id, address) values (?, ?)", (user_id, address))

    database.commit()
    database.close()

    return address

def user_exists(user_id):
    database = sqlite3.connect("tipkoto.db")
    db = database.cursor()

    if len([row for row in db.execute("select * from users where user_id = ?", (user_id,))]) == 0:
        exists = False

    else:
        exists = True

    database.close()

    return exists

def get_address_of(user_id):
    database = sqlite3.connect("tipkoto.db")
    db = database.cursor()

    address = db.execute("select address from users where user_id = ?", (user_id,)).fetchone()[0]

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

def is_amount(argument):
    if argument.lower() == "all" or argument == "全額":
        return True

    try:
        float(argument)

    except ValueError:
        return False

    if "e" in argument.lower():
        return False

    return True

def get_command(text):
    text = text.replace("\n", " ")
    text = text.replace("　", " ")

    while True:
        place = text.find("@tipkotone")

        if place == -1:
            return [None]

        else:
            text = text[place + 11:]
            command = re.split(" +", text)
            command[0] = command[0].lower()

            if command[0] in ["withdraw", "出金",
                              "tip", "投げ銭", "投銭",
                              "check", "確認"]:

                return command

            else:
                for cmd in ["help", "ヘルプ",
                            "follow me", "フォローミー",
                            "balance", "残高",
                            "deposit", "入金",
                            "address", "アドレス",
                            "hello", "hi", "こんにちは", "はじめまして"]:

                    if re.match(cmd, text.lower()):
                        return [cmd]

def round_down(amount_string):
    if "." in amount_string:
        return amount_string[:amount_string.find(".") + 9]

    else:
        return amount_string

def send_tweet(tweet, status_id):
    tweet = tweet + "\n\n" + "".join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
    api.update_status(status = tweet, in_reply_to_status_id = status_id)

def on_tweet(status):
    if status.text.find("RT ") != -1:
        if status.text.find("RT ") == 0:
            return

        elif status.text.find(" RT ") != -1:
            return

    if status.text.find("QT ") != -1:
        if status.text.find("QT ") == 0:
            return

        elif status.text.find(" QT ") != -1:
            return

    if status.user.screen_name == "tipkotone":
        return

    if status.text.find("@tipkotone") == -1:
        return

    else:
        name = status.user.name
        screen_name = status.user.screen_name
        user_id = "twitter-tipkotone-" + str(status.user.id)
        command = get_command(status.text)

        if command[0] == None:
            return

        elif command[0] in ["help", "ヘルプ"]:
            logger.info("%s(@%s) Help" % (name, screen_name))
            tweet = "@" + screen_name + " tipkotoneの使い方はこちらです！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

        elif command[0] in ["follow me", "フォローミー"]:
            logger.info("%s(@%s) Follow" % (name, screen_name))
            
            user = api.get_user(screen_name)
            if not user.following:
                api.create_friendship(screen_name)
                logger.info("--> Follow")
                tweet = "@" + screen_name + " フォローしました！"

            else:
                logger.info("--> Already follow")
                tweet = "@" + screen_name + " すでにフォローしています！"

        elif user_exists(user_id):
            if command[0] in ["withdraw", "出金"]:
                logger.info("%s(@%s) Withdraw" % (name, screen_name))

                if len(command) < 3:
                    logger.info("--> Arguments shortage")
                    tweet = "@" + screen_name + " tipkotoneの使い方はこちらです！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

                else:
                    balance, confirming_balance = get_balance_of(user_id)

                    if is_amount(command[1]):
                        if address_is_ok(command[2]):
                            if command[1].lower() in ["all", "全額"]:
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal(round_down(command[1]))

                            to_address = command[2]

                        else:
                            logger.info("--> Invalid address")
                            tweet = "@" + screen_name + " アドレスが間違っています・・・"
                            send_tweet(tweet, status.id)
                            return

                    elif is_amount(command[2]):
                        if address_is_ok(command[1]):
                            if command[2].lower() in ["all", "全額"]:
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal(round_down(command[2]))

                            to_address = command[1]

                        else:
                            logger.info("--> Invalid address")
                            tweet = "@" + screen_name + " アドレスが間違っています・・・"
                            send_tweet(tweet, status.id)
                            return

                    else:
                        logger.info("--> Invalid amount")
                        tweet = "@" + screen_name + " 金額が間違っています・・・"
                        send_tweet(tweet, status.id)
                        return

                    change = balance - amount - Decimal("0.0001")

                    if amount_is_ok(balance, amount, change):
                        from_address = get_address_of(user_id)

                        params = get_params(from_address, to_address, balance, amount, change)
                        koto.call("z_sendmany", *params)

                        logger.info("--> {0:f}KOTO ".format(amount) + "to " + to_address)

                        tweet = "@" + screen_name + " {0:f}KOTO を ".format(amount) + to_address + " に出金しました！"

                    elif change < 0:
                        logger.info("--> Insufficient balance")
                        tweet = "@" + screen_name + " 残高が足りません・・・ {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming)".format(confirming_balance)

                    else:
                        logger.info("--> Invalid amount")
                        tweet = "@" + screen_name + " この金額では出金できません・・・"

            elif command[0] in ["tip", "投げ銭", "投銭"]:
                logger.info("%s(@%s) Tip" % (name, screen_name))

                if len(command) < 3:
                    logger.info("--> Arguments shortage")
                    tweet = "@" + screen_name + " tipkotoneの使い方はこちらです！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

                else:
                    balance, confirming_balance = get_balance_of(user_id)

                    if is_amount(command[1]):
                        if command[2].startswith("@"):
                            if command[1].lower() in ["all", "全額"]:
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal(round_down(command[1]))

                            to_screen_name = command[2][1:]

                        else:
                            logger.info("--> To screen name is incorrect")
                            tweet = "@" + screen_name + " 宛先が間違っています・・・"
                            send_tweet(tweet, status.id)
                            return

                    elif is_amount(command[2]):
                        if command[1].startswith("@"):
                            if command[2].lower() in ["all", "全額"]:
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal(round_down(command[2]))

                            to_screen_name = command[1][1:]

                        else:
                            logger.info("--> To screen name is incorrect")
                            tweet = "@" + screen_name + " 宛先が間違っています・・・"
                            send_tweet(tweet, status.id)
                            return

                    else:
                        logger.info("--> Invalid amount")
                        tweet = "@" + screen_name + " 金額が間違っています・・・"
                        send_tweet(tweet, status.id)
                        return

                    change = balance - amount - Decimal("0.0001")

                    if to_screen_name == screen_name:
                        logger.info("--> To user is from user")
                        tweet = "@" + screen_name + " 自分自身には投げ銭できません！"

                    elif to_screen_name == "tipkotone":
                        logger.info("--> No thank you but I appreciate it")
                        tweet = "@" + screen_name + " お気持ちだけでうれしいです！ ありがとう！"

                    else:
                        try:
                            to_user = api.get_user(to_screen_name)

                        except:
                            logger.info("--> To user is not found")
                            tweet = "@" + screen_name + " 宛先(@%s)が見つかりませんでした・・・" % (to_screen_name)
                            send_tweet(tweet, status.id)
                            return

                        to_name = to_user.name
                        to_user_id = "twitter-tipkotone-" + str(to_user.id)

                        if user_exists(to_user_id):
                            if amount_is_ok(balance, amount, change):
                                from_address = get_address_of(user_id)
                                to_address = get_address_of(to_user_id)

                                params = get_params(from_address, to_address, balance, amount, change)
                                koto.call("z_sendmany", *params)

                                logger.info("--> {0:f}KOTO ".format(amount) + "to %s(@%s)" % (to_name, to_screen_name))

                                tweet = "@" + screen_name + " @" + to_screen_name + " " + name + "さんから " + to_name + "さんへ お心付けです！ {0:f}KOTO".format(amount)

                            elif change < 0:
                                logger.info("--> Insufficient balance")
                                tweet = "@" + screen_name + " 残高が足りません・・・ {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming)".format(confirming_balance)

                            else:
                                logger.info("--> Invalid amount")
                                tweet = "@" + screen_name + " この額では投げ銭できません・・・"

                        else:
                            logger.info("--> To user has not used tipkotone yet")
                            tweet = "@" + screen_name + " %s(@%s)" % (to_name, to_screen_name) + "さんはtipkotoneをまだ使ってないみたい・・・"

            elif command[0] in ["balance", "残高"]:
                logger.info("%s(@%s) Balance" % (name, screen_name))
                balance, confirming_balance = get_balance_of(user_id)
                logger.info("--> {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming)".format(confirming_balance))

                if confirming_balance == 0:
                    tweet = "@" + screen_name + " " + name + "さんの残高は {0:f}KOTO です！".format(balance)

                else:
                    tweet = "@" + screen_name + " " + name + "さんの残高は {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming) です！".format(confirming_balance)

            elif command[0] in ["deposit", "入金"]:
                logger.info("%s(@%s) Deposit" % (name, screen_name))
                address = get_address_of(user_id)
                logger.info("--> " + address)
                tweet = "@" + screen_name + " このアドレスに送金してください！ " + address

            elif command[0] in ["address", "アドレス"]:
                logger.info("%s(@%s) Address" % (name, screen_name))
                address = get_address_of(user_id)
                logger.info("--> " + address)
                tweet = "@" + screen_name + " " + name + "さんのアドレスはこちらです！ " + address

            elif command[0] in ["check", "確認"]:
                logger.info("%s(@%s) Check" % (name, screen_name))

                if len(command) < 2:
                    logger.info("--> Arguments shortage")
                    tweet = "@" + screen_name + " tipkotoneの使い方はこちらです！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

                elif not command[1].startswith("@"):
                    logger.info("--> To screen name is incorrect")
                    tweet = "@" + screen_name + " ユーザー名が間違っています・・・"

                else:
                    to_screen_name = command[1][1:]

                    try:
                        to_user = api.get_user(to_screen_name)

                    except:
                        logger.info("--> To user is not found")
                        tweet = "@" + screen_name + " 確認相手(@%s)が見つかりませんでした・・・" % (to_screen_name)
                        send_tweet(tweet, status.id)
                        return

                    to_name = to_user.name
                    to_user_id = "twitter-tipkotone-" + str(to_user.id)

                    if user_exists(to_user_id):
                        logger.info("--> To user already uses tipkotone")
                        tweet = "@" + screen_name + " %s(@%s)" % (to_name, to_screen_name) + "さんはtipkotoneを使っています！"

                    else:
                        logger.info("--> To user has not used tipkotone yet")
                        tweet = "@" + screen_name + " %s(@%s)" % (to_name, to_screen_name) + "さんはtipkotoneをまだ使ってないみたい・・・"


            elif command[0] in ["hello", "hi", "こんにちは"]:
                tweet = "@" + screen_name + " こんにちは！"

            elif command[0] == "はじめまして":
                tweet = "@" + screen_name + " もう！ はじめましてじゃないでしょ！"

            else:
                return

        elif command[0] in ["hello", "hi", "address", "こんにちは", "はじめまして", "アドレス"]:
            logger.info("%s(@%s) First contact" % (name, screen_name))
            address = insert_data(user_id)
            logger.info("--> " + address)
            tweet = "@" + screen_name + " はじめまして！ " + name + "さんの入金用アドレスを用意しました！ " +  address

        else:
            return

        send_tweet(tweet, status.id)

class Listener(StreamListener):
    def on_connect(self):
        logger.info("Connect")

        return

    def on_status(self, status):
        on_tweet(status)

        return True

# on_dataは自分がオーバーライドしたらうまく動かへんからほっとく。他のがFalseを返さんかったら問題ないはず。

    def on_exception(self, exception):
        logger.error("Exception : " + str(exception))

        return

    def on_limit(self, track):
        logger.warning("Limit : " + str(track))

        return

    def on_error(self, status_code):
        logger.error("Error : " + str(status_code))

        return True

    def on_timeout(self):
        logger.info("Timeout")

        return True

    def on_disconnect(self, notice):
        logger.info("Disconnect : " + str(notice))

        return

    def on_warning(self, notice):
        logger.warning("Warning : " + str( notice))

        return

if __name__ == "__main__":
    logger.info("Start")
    while True:
        try:
            stream = Stream(auth, Listener(), secure = True)
            stream.userstream()

        except KeyboardInterrupt:
            logger.info("Stop")
            break

        except:
            pass


