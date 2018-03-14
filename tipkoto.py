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

    return True

def on_tweet(status):
    if status.text.find("RT") == -1 and status.text.find("QT") == -1 and status.user.screen_name != "tipkotone":
        if status.text.find("@tipkotone") == -1:
            return

        name = status.user.name
        screen_name = status.user.screen_name
        user_id = "twitter-tipkotone-" + str(status.user.id)
        command = status.text[(status.text.find("@tipkotone") + 11):]

        if re.search("help", command.lower()) or re.search("ヘルプ", command):
            logger.info("%s(@%s) Help" % (name, screen_name))
            tweet = "@" + screen_name + " tipkotoの使い方はこちら！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

        elif re.match("follow me", command.lower()) or re.match("フォローミー", command):
            logger.info("%s(@%s) Follow me" % (name, screen_name))

            user = api.get_user(screen_name)
            if not user.following:
                api.create_friendship(screen_name)
                logger.info("--> Follow")
                tweet = "@" + screen_name + " フォローしました！"

            else:
                logger.info("--> Already follow")
                tweet = "@" + screen_name + " すでにフォローしています！"

        elif user_exists(user_id):
            if re.match("withdraw", command.lower()) or re.match("出金", command):
                logger.info("%s(@%s) Withdraw" % (name, screen_name))

                command_arguments = re.split(" +", command.replace("\n", " "))

                if len(command_arguments) < 3:
                    logger.info("--> Arguments shortage")
                    tweet = "@" + screen_name + " tipkotoの使い方はこちら！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

                else:
                    if address_is_ok(command_arguments[2]):
                        if is_amount(command_arguments[1]):
                            balance, confirming_balance = get_balance_of(user_id)

                            if command_arguments[1].lower() == "all" or command_arguments[1] == "全額":
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal("{0:.8f}".format(float(command_arguments[1])))

                            change = balance - amount - Decimal("0.0001")

                            if amount_is_ok(balance, amount, change):
                                from_address = get_address_of(user_id)
                                to_address = command_arguments[2]

                                params = get_params(from_address, to_address, balance, amount, change)
                                koto.call("z_sendmany", *params)

                                logger.info("--> {0:f}KOTO ".format(amount) + "to " + to_address)

                                tweet = "@" + screen_name + " {0:f}KOTO を ".format(amount) + to_address + " に出金しました！"

                            elif change < 0:
                                logger.info("--> Insufficient balance")
                                tweet = "@" + screen_name + " 残高が足りません・・・ {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming)".format(confirming_balance)

                            else:
                                logger.info("--> Invalid amount")
                                tweet = "@" + screen_name + " この額では出金できません・・・"

                        else:
                            logger.info("--> Amount argument is incorrect")
                            tweet = "@" + screen_name + " 数字と認識できませんでした・・・ ちゃんと半角数字になってるか確認してみて！"

                    else:
                        logger.info("--> Invalid address")
                        tweet = "@" + screen_name + " このアドレスには出金できません・・・"

            elif re.match("tip", command.lower()) or re.match("投げ銭", command) or re.match("投銭", command):
                logger.info("%s(@%s) Tip" % (name, screen_name))
                command_arguments = re.split(" +", command.replace("\n", " "))

                if len(command_arguments) < 3:
                    logger.info("--> Arguments shortage")
                    tweet = "@" + screen_name + " tipkotoの使い方はこちら！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"
                    
                elif not command_arguments[2].startswith("@"):
                    logger.info("--> To screen name is incorrect")
                    tweet = "@" + screen_name + " tipkotoの使い方はこちら！ https://github.com/akarinS/tipkoto/blob/master/HowToUse.md"

                else:
                    to_screen_name = command_arguments[2][1:]

                    if to_screen_name == screen_name:
                        logger.info("--> To user is from user")
                        tweet = "@" + screen_name + " 自分自身には投げ銭できません！"
                        tweet = tweet + "\n\n" + ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
                        api.update_status(status = tweet, in_reply_to_status_id = status.id)
                        return

                    if to_screen_name == "tipkotone":
                        logger.info("--> No thank you but I appreciate it")
                        tweet = "@" + screen_name + " お気持ちだけでうれしいです！ ありがとう！"
                        tweet = tweet + "\n\n" + ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
                        api.update_status(status = tweet, in_reply_to_status_id = status.id)
                        return

                    try:
                        to_user = api.get_user(to_screen_name)

                    except:
                        logger.info("--> To user is not found")
                        tweet = "@" + screen_name + " 宛先（@%s）が見つかりませんでした・・・" % (to_screen_name)
                        tweet = tweet + "\n\n" + ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
                        api.update_status(status = tweet, in_reply_to_status_id = status.id)
                        return

                    to_name = to_user.name
                    to_user_id = "twitter-tipkotone-" + str(to_user.id)

                    if user_exists(to_user_id):
                        if is_amount(command_arguments[1]):
                            balance, confirming_balance = get_balance_of(user_id)

                            if command_arguments[1].lower() == "all" or command_arguments[1] == "全額":
                                amount = balance - Decimal("0.0001")

                            else:
                                amount = Decimal("{0:.8f}".format(float(command_arguments[1])))

                            change = balance - amount - Decimal("0.0001")

                            if amount_is_ok(balance, amount, change):
                                from_address = get_address_of(user_id)
                                to_address = get_address_of(to_user_id)

                                params = get_params(from_address, to_address, balance, amount, change)
                                koto.call("z_sendmany", *params)

                                logger.info("--> {0:f}KOTO ".format(amount) + "to %s(@%s)" % (to_name, to_screen_name))

                                tweet = "@" + screen_name + " @" + to_screen_name + " " + name + "さんから" + to_name + "さんへ {0:f}KOTO の投げ銭です！".format(amount)

                            elif change < 0:
                                logger.info("--> Insufficient balance")
                                tweet = "@" + screen_name + " 残高が足りません・・・ {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming)".format(confirming_balance)

                            else:
                                logger.info("--> Invalid amount")
                                tweet = "@" + screen_name + " この額では投げ銭できません・・・"

                        else:
                            logger.info("--> Amount argument is incorrect")
                            tweet = "@" + screen_name + " 数字と認識できませんでした・・・　ちゃんと半角数字になってるか確認してみて！"

                    else:
                        logger.info("--> To user has not used tipkoto yet")
                        tweet = "@" + screen_name + " %s（@%s）" % (to_name, to_screen_name) + "さんはtipkotoをまだ使ってないみたい・・・"

            elif re.search("balance", command.lower()) or re.search("残高", command):
                logger.info("%s(@%s) Balance" % (name, screen_name))
                balance, confirming_balance = get_balance_of(user_id)
                logger.info("--> {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming)".format(confirming_balance))

                if confirming_balance == 0:
                    tweet = "@" + screen_name + " " + name + "さんの残高は {0:f}KOTO です！".format(balance)

                else:
                    tweet = "@" + screen_name + " " + name + "さんの残高は {0:f}KOTO ".format(balance) + "(+{0:f}KOTO confirming) です！".format(confirming_balance)

            elif re.search("deposit", command.lower()) or re.search("入金", command):
                logger.info("%s(@%s) Deposit" % (name, screen_name))
                address = get_address_of(user_id)
                logger.info("--> " + address)
                tweet = "@" + screen_name + " このアドレスに送金してね！ " + address

            elif re.search("address", command.lower()) or re.search("アドレス", command):
                logger.info("%s(@%s) Address" % (name, screen_name))
                address = get_address_of(user_id)
                logger.info("--> " + address)
                tweet = "@" + screen_name + " " + name + "さんのアドレスはこちら！ " + address

            elif re.search("hello", command.lower()) or re.search("Hi", command.lower()) or re.search("こんにちは", command):
                tweet = "@" + screen_name + " こんにちは！"

            elif re.search("はじめまして", command):
                tweet = "@" + screen_name + " もう！ はじめましてじゃないでしょ！"

            else:
                return

        elif re.search("hello", command.lower()) or re.search("hi", command.lower()) or re.search("こんにちは", command) or re.search("はじめまして", command) or re.search("address", command.lower()) or re.search("アドレス", command):
            logger.info("%s(@%s) First contact" % (name, screen_name))
            address = insert_data(user_id)
            logger.info("--> " + address)
            tweet = "@" + screen_name + " はじめまして！ " + name + "さんの入金用アドレスを用意しました！ " +  address

        else:
            return

        tweet = tweet + "\n\n" + ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
        api.update_status(status = tweet, in_reply_to_status_id = status.id)

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


