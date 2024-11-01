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

        filtered_history = [
            rec for rec in user_history if start_date <= datetime.strptime(rec.split(",")[0], "%Y-%m-%d %H:%M:%S") <= end_date
        ]

        if not filtered_history:
            response = f"No {selectedType} records found between {start_date.date()} and {end_date.date()}."
            bot.reply_to(message, response)
            return response

        pdf_status = generate_pdf(filtered_history, selectedType, chat_id, bot)
        bot.reply_to(message, pdf_status)  # Send feedback message about PDF generation status
        return pdf_status

    except ValueError:
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
        date, category, amount = rec.split(",")
        date, time = date.split(" ")
        rec_str = f"{amount}$ {category} {selectedType.lower()} on {date} at {time}"
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
    pdf_path = f"history_{chat_id}.png"  # Changed to PNG
    try:
        plt.savefig(pdf_path)
        plt.close()
        print(f"PDF saved to {pdf_path}")  # Debugging output
    except Exception as e:
        response = f"Error saving the PDF: {str(e)}"
        bot.reply_to(chat_id, response)
        return response

    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as pdf_file:
                bot.send_document(chat_id, pdf_file)
            os.remove(pdf_path)
            response = "PDF generated and sent successfully!"
            return response
        except Exception as e:
            response = f"Failed to send PDF: {str(e)}"
            bot.reply_to(chat_id, response)
            return response
    else:
        response = "Failed to generate PDF."
        bot.reply_to(chat_id, response)
        return response



