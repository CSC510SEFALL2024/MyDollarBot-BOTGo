#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import telebot
import time
import helper
import edit
import history
import display
import estimate
import delete
import add
import budget
import category
import extract
import sendEmail
import add_recurring
import receipt
import process_csv
import add_income
import pdf
import savings_tracker
from datetime import datetime
from jproperties import Properties
import display_currency
import chatGPT_ext
import get_csv
import scan_receipt
import csv_between_dates

configs = Properties()

with open('user.properties', 'rb') as read_prop:
    configs.load(read_prop)

api_token = str(configs.get('api_token').data)

bot = telebot.TeleBot(api_token)

telebot.logger.setLevel(logging.INFO)

option = {}


# Define listener for requests by user
def listener(user_requests):
    for req in user_requests:
        if (req.content_type == 'text'):
            print("{} name:{} chat_id:{} \nmessage: {}\n".format(
                str(datetime.now()), str(req.chat.first_name), str(req.chat.id), str(req.text)))


bot.set_update_listener(listener)


# defines how the /start and /help commands have to be handled/processed
@bot.message_handler(commands=['start', 'menu'])
def start_and_menu_command(m):
    helper.read_json()
    global user_list
    chat_id = m.chat.id

    text_intro = "Welcome to MyDollarBot - a simple solution to track your expenses and manage them ! \n Please select the options from below for me to assist you with: \n\n"
    commands = helper.getCommands()
    for c in commands:  # generate help text out of the commands dictionary defined at the top
        text_intro += "/" + c + ": "
        text_intro += commands[c] + "\n\n"
    bot.send_message(chat_id, text_intro)
    return True


# defines how the /new command has to be handled/processed
# function to add an expense
@bot.message_handler(commands=['add_expense'])
def command_add(message):
    add.run(message, bot)


# function to add recurring expenses
@bot.message_handler(commands=['add_recurring'])
def command_add_recurring(message):
    add_recurring.run(message, bot)


# function to fetch expenditure history of the user
@bot.message_handler(commands=['history'])
def command_history(message):
    history.run(message, bot)


# function to edit date, category or cost of a transaction
@bot.message_handler(commands=['edit'])
def command_edit(message):
    edit.run(message, bot)


# function to display total expenditure
@bot.message_handler(commands=['display'])
def command_display(message):
    display.run(message, bot)


# function to estimate future expenditure
@bot.message_handler(commands=['estimate'])
def command_estimate(message):
    estimate.run(message, bot)


# handles "/delete" command
@bot.message_handler(commands=['delete'])
def command_delete(message):
    delete.run(message, bot)


@bot.message_handler(commands=['budget'])
def command_budget(message):
    budget.run(message, bot)


@bot.message_handler(commands=['category'])
def command_category(message):
    category.run(message, bot)


@bot.message_handler(commands=['extract'])
def command_extract(message):
    extract.run(message, bot)


@bot.message_handler(commands=['sendEmail'])
def command_sendEmail(message):
    sendEmail.run(message, bot)


@bot.message_handler(commands=['receipt'])
def command_receipt(message):
    receipt.command_receipt(message, bot)


@bot.message_handler(commands=['add_income'])
def command_add_income(message):
    add_income.run(message, bot)


@bot.message_handler(commands=['pdf'])
def command_category(message):
    pdf.run(message, bot)
    
@bot.message_handler(commands=['csv'])
def command_category(message):
    get_csv.run(message, bot)
    
@bot.message_handler(commands=['scan_receipt'])
def command_scan_receipt(message):
    scan_receipt.run(message, bot)

@bot.message_handler(commands=['csv_between_dates'])
def command_csv_between_dates(message):
    csv_between_dates.run(message, bot)


@bot.message_handler(commands=['savings_tracker'])
def command_savings_tracker(message):
    savings_tracker.run(message, bot)


# not used
def addUserHistory(chat_id, user_record):
    global user_list
    if (not (str(chat_id) in user_list)):
        user_list[str(chat_id)] = []
    user_list[str(chat_id)].append(user_record)
    return user_list


@bot.message_handler(commands=["upload"])
def bulkInsert(message):
    '''
    This function is used to add bulk expenses using uploading a csv file.
    :param message: telebot.types.Message object representing the message object
    :return: None
    '''
    document = open('data/records.csv', 'rb')
    bot.send_message(str(message.chat.id), "Please update the below csv and repload it with data.")
    bot.register_next_step_handler(message, handle_document_csv)
    bot.send_document(str(message.chat.id), document)


def handle_document_csv(message):
    process_csv.process_csv_file(message=message, bot=bot)


@bot.message_handler(commands=['chat'])
def command_history(message):
    chatGPT_ext.run(message, bot)


@bot.message_handler(commands=['DisplayCurrency'])
def command_history(message):
     display_currency.run(message, bot)


def main():
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        logging.exception(str(e))
        time.sleep(10)
        print("Connection Timeout")


if __name__ == '__main__':
    main()
