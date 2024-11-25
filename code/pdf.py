import helper
import logging
from telebot import types
from matplotlib import pyplot as plt
from datetime import datetime
import os

def run(message, bot):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    options = helper.getIncomeOrExpense()
    markup.row_width = 2
    if not options:
        bot.reply_to(message, "No options available.")
        return
    for c in options.values():
        markup.add(c)
    msg = bot.reply_to(message, 'Select Income or Expense', reply_markup=markup)
    bot.register_next_step_handler(msg, post_type_selection, bot)

def post_type_selection(message, bot):
    try:
        chat_id = message.chat.id
        selectedType = message.text
        helper.read_json()
        
        msg = bot.reply_to(
            message, "Enter start date (YYYY-MM-DD):"
        )
        bot.register_next_step_handler(msg, get_start_date, bot, selectedType, chat_id)
    except Exception as e:
        logging.exception(str(e))
        return str(e)  # Return the exception message for testing


def get_start_date(message, bot, selectedType, chat_id):
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d")
        msg = bot.reply_to(
            message, "Enter end date (YYYY-MM-DD):"
        )
        bot.register_next_step_handler(
            msg, get_end_date, bot, selectedType, chat_id, start_date
        )
    except ValueError:
        response = "Invalid date format. Please use YYYY-MM-DD."
        bot.reply_to(message, response)
        return response

def get_end_date(message, bot, selectedType, chat_id, start_date):
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d")
        
        if end_date < start_date:
            response = "End date cannot be before start date. Please try again."
            bot.reply_to(message, response)
            return response

        user_history = helper.getUserHistory(chat_id, selectedType) or []
        filtered_history = []
        for record in user_history:
            try:
                date_time, category, amount = record.split(",")
                date, _ = date_time.split(" ")
                record_date = datetime.strptime(date, "%d-%b-%Y")
                
                if start_date <= record_date <= end_date:
                    filtered_history.append([date, category, float(amount)])
            except ValueError:
                logging.warning(f"Skipping malformed record: {record}")
                continue
        print(filtered_history)
        if not filtered_history:
            bot.send_message(chat_id, "No records found within the selected date range!")
            return
        
        pdf_status = generate_pdf(filtered_history, selectedType, chat_id, bot)
        #bot.reply_to(message, pdf_status)  # Send feedback message about PDF generation status
        return pdf_status

    except ValueError as e:
        print(e)
        response = "Invalid date format. Please use YYYY-MM-DD."
        bot.reply_to(message, response)
        return response
    except Exception as e:
        response = f"An error occurred: {e}"
        logging.exception(str(e))
        bot.reply_to(message, response)
        return response


def generate_pdf(user_history, selectedType, chat_id, bot):
    if not user_history:
        response = "No records to generate a PDF."
        bot.reply_to(chat_id, response)
        return response
    
    fig, ax = plt.subplots()
    top = 0.8

    for rec in user_history:
        date, category, amount = rec[0], rec[1], rec[2]
        rec_str = f"{amount}$ {category} {selectedType.lower()} on {date}ß"
        plt.text(
            0,
            top,
            rec_str,
            horizontalalignment="left",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=12,
            bbox=dict(facecolor="red", alpha=0.3),
        )
        top -= 0.15

    plt.axis("off")
    #pdf_path = f"history_{chat_id}.png"  # Changed to PNG
    try:
        plt.savefig("history.pdf")
        plt.close()
        bot.send_document(chat_id, open("history.pdf", "rb"))
        print(f"PDF saved.")  # Debugging output
    except Exception as e:
        response = f"Error saving the PDF: {str(e)}"
        bot.reply_to(chat_id, response)
        return response




