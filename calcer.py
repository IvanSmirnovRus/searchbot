import sys
import logging
import telegram
import urllib
import json
from time import sleep
try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError  # python 2


class Operator(object):
    def __init__(self, symbol):
        self.symbol = symbol
        self.priority = {'+': 1,
                         '-': 1,
                         '*': 2,
                         '/': 2,
                         '%': 2,
                         '**': 3}[symbol]
        self.associativity = {'+': 'l',
                              '-': 'l',
                              '*': 'l',
                              '/': 'l',
                              '%': 'l',
                              '**': 'r'}[symbol]

    def __call__(self, first_operand, second_operand):
        if self.symbol == '/':
            return first_operand / second_operand
        elif self.symbol == '*':
            return first_operand * second_operand
        elif self.symbol == '-':
            return first_operand - second_operand
        elif self.symbol == '+':
            return first_operand + second_operand
        elif self.symbol == '**':
            return first_operand ** second_operand

    def __str__(self):
        return self.symbol


class Stack(object):

    def __init__(self):
        self.stack = []

    def __str__(self):
        return str(self.stack)

    def empty(self):
        if len(self.stack) > 0:
            return 0
        else:
            return 1

    def top(self):
        if not self.empty():
            return self.stack[-1]
        else:
            return "Stack is Empty!"

    def push(self, value):
        self.stack.append(value)
        return value

    def pop(self):
        if not self.empty():
            top = self.top()
            self.stack = self.stack[:-1]
            return top
        else:
            return "Stack is Empty!"


def isoperator(symbol):
    if symbol in ['+', '-', '*', '/', '**']:
        return True
    else:
        return False


class RPN(object):
    def __init__(self, expression):
        self.rpn = []
        stack = Stack()
        for symbol in expression.split():
            if symbol.isdigit():
                self.rpn.append(symbol)
            if not isoperator(symbol) and symbol.startswith('-'):
                self.rpn.append('!' + symbol[1:])
            if '.' in symbol:
                self.rpn.append(symbol)
            elif isoperator(symbol):
                operator = Operator(symbol)
                while (not stack.empty() and
                       isinstance(stack.top(), Operator) and
                       (operator.associativity == 'l' and
                        operator.priority <= stack.top().priority or
                        operator.associativity == 'r' and
                        operator.priority < stack.top().priority)):
                    self.rpn.append(stack.pop())
                stack.push(operator)
            elif symbol == '(':
                stack.push(symbol)
            elif symbol == ')':
                while not stack.empty() and stack.top() != '(':
                    self.rpn.append(stack.pop())
                if stack.top() == '(':
                    stack.pop()
                else:
                    print 'Incorrect expression!'
        while not stack.empty():
            self.rpn.append(stack.pop())

    def __str__(self):
        return ''.join([str(x) for x in self.rpn])

    def calc(self):
        stack = Stack()
        for symbol in self.rpn:
            if isinstance(symbol, Operator):
                b = stack.pop()
                a = stack.pop()
                stack.push(symbol(float(a), float(b)))
            elif symbol.isdigit():
                stack.push(symbol)
            elif symbol.startswith('!'):
                stack.push('-' + symbol[1:])
            elif '.' in symbol:
                stack.push(symbol)
        if stack.top() == int(stack.top()):
            return int(stack.pop())
        else:
            return stack.pop()


def main():
    # Telegram Bot Authorization Token
    bot = telegram.Bot('134059776:AAHp_iQKrgoonzmd_5pdacW7WWd8EiTmP9c')

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.getUpdates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            update_id = calcer(bot, update_id)
        except telegram.TelegramError as e:
            # These are network problems with Telegram.
            if e.message in ("Bad Gateway", "Timed out"):
                sleep(1)
            elif e.message == "Unauthorized":
                # The user has removed or blocked the bot.
                update_id += 1
            else:
                raise e
        except URLError as e:
            # These are network problems on our end.
            sleep(1)


def search(bot, update_id):
    template = 'https://yandex.ru/suggest-combo/firefox/?brandid=yandexpart='
    # Request updates after the last update_id
    for update in bot.getUpdates(offset=update_id, timeout=10):
        # chat_id is required to reply to any message
        chat_id = update.message.chat_id
        update_id = update.update_id + 1
        message = update.message.text

        if message:
            # Reply to the message
            message = message.encode('utf-8')
            f = urllib.urlopen(template + message)
            answer = json.loads(f.read())
            urls = answer['instant-search-suggest']
            descriptions = answer['descriptions']
            if len(urls):
                url = urls[0]
                if len(descriptions):
                    title = descriptions[0]['title']
                    result = title + '\n' + url
                else:
                    result = url
            else:
                result = "Sorry, I am too stupid!"
            bot.sendMessage(chat_id=chat_id,
                            text=result)
    return update_id


def calcer(bot, update_id):
    for update in bot.getUpdates(offset=update_id, timeout=10):
        chat_id = update.message.chat_id
        update_id = update.update_id + 1
        message = update.message.text

        if message:
            result = RPN(message).calc()
            bot.sendMessage(chat_id=chat_id,
                            text=result)
    return update_id

if __name__ == '__main__':
    main()
