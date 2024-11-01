import helper
import logging
from telebot import types
import pandas as pd
import xlsxwriter
import os
from datetime import datetime

def run(message, bot):
    """
    Initial function to handle the /csv command
    """
    try:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        options = helper.getIncomeOrExpense()
        markup.row_width = 2
        for c in options.values():
            markup.add(c)
        msg = bot.reply_to(message, 'Select Income or Expense', reply_markup=markup)
        bot.register_next_step_handler(msg, post_type_selection, bot)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"Error in initial setup: {str(e)}")

def post_type_selection(message, bot):
    """
    Handles the selection of Income or Expense and prompts for date range.
    """
    try:
        chat_id = message.chat.id
        selected_type = message.text
        # Save selected type and proceed to start date prompt
        bot.send_message(chat_id, "Please enter the start date in yyyy-mm-dd format.")
        bot.register_next_step_handler(message, get_start_date, bot, selected_type)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"Error in selection: {str(e)}")

def get_start_date(message, bot, selected_type):
    """
    Prompts the user to enter the start date and validates the input.
    """
    try:
        chat_id = message.chat.id
        start_date = message.text

        # Validate start date format
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            bot.send_message(chat_id, "Invalid date format. Please enter the start date in yyyy-mm-dd format.")
            bot.register_next_step_handler(message, get_start_date, bot, selected_type)
            return

        # Proceed to prompt for end date
        bot.send_message(chat_id, "Please enter the end date in yyyy-mm-dd format.")
        bot.register_next_step_handler(message, get_end_date, bot, selected_type, start_date_obj)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"Error in start date input: {str(e)}")

def get_end_date(message, bot, selected_type, start_date_obj):
    """
    Prompts the user to enter the end date, validates the input, and generates the CSV.
    """
    try:
        chat_id = message.chat.id
        end_date = message.text

        # Validate end date format
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            bot.send_message(chat_id, "Invalid date format. Please enter the end date in yyyy-mm-dd format.")
            bot.register_next_step_handler(message, get_end_date, bot, selected_type, start_date_obj)
            return

        # Ensure start date is before or equal to end date
        if start_date_obj > end_date_obj:
            bot.send_message(chat_id, "End date must be after the start date. Please enter the end date again.")
            bot.register_next_step_handler(message, get_end_date, bot, selected_type, start_date_obj)
            return

        # Fetch and filter user history by date range
        user_history = helper.getUserHistory(chat_id, selected_type)
        if user_history is None or len(user_history) == 0:
            bot.send_message(chat_id, "No records found!")
            return

        # Filter data and create CSV
        generate_csv(chat_id, bot, selected_type, user_history, start_date_obj, end_date_obj)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"Error in end date input: {str(e)}")

def generate_csv(chat_id, bot, selected_type, user_history, start_date_obj, end_date_obj):
    """
    Generates and sends a CSV file based on the filtered user history within the date range.
    """
    try:
        # Convert user history to DataFrame and filter by date range
        data = []
        for record in user_history:
            try:
                date_time, category, amount = record.split(",")
                date, _ = date_time.split(" ")
                record_date = datetime.strptime(date, "%d-%b-%Y")
                
                if start_date_obj <= record_date <= end_date_obj:
                    data.append([date, category, float(amount)])
            except ValueError:
                logging.warning(f"Skipping malformed record: {record}")
                continue
        
        if not data:
            bot.send_message(chat_id, "No records found within the selected date range!")
            return

        # Create DataFrame
        df = pd.DataFrame(data, columns=['Date', 'Category', 'Amount'])
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
        df['Month'] = df['Date'].dt.to_period('M')

        # Create filename with timestamp and chat_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{chat_id}_{timestamp}.xlsx"

        # Create pivot tables and charts
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Transactions', index=False)
            monthly_pivot = df.pivot_table(values='Amount', index='Month', aggfunc='sum')
            monthly_pivot.to_excel(writer, sheet_name='Monthly_Spending')
            category_pivot = df.pivot_table(values='Amount', index='Category', aggfunc='sum')
            category_pivot.to_excel(writer, sheet_name='Category_Spending')

            workbook = writer.book
            chart1 = workbook.add_chart({'type': 'line'})
            chart1.add_series({
                'name': 'Monthly Spending',
                'categories': ['Monthly_Spending', 1, 0, len(monthly_pivot), 0],
                'values': ['Monthly_Spending', 1, 1, len(monthly_pivot), 1],
                'line': {'color': 'blue'},
            })
            chart1.set_title({'name': 'Spending per Month'})
            writer.sheets['Monthly_Spending'].insert_chart('D2', chart1)

            chart2 = workbook.add_chart({'type': 'pie'})
            chart2.add_series({
                'name': 'Category Spending',
                'categories': ['Category_Spending', 1, 0, len(category_pivot), 0],
                'values': ['Category_Spending', 1, 1, len(category_pivot), 1],
            })
            chart2.set_title({'name': 'Spending by Category'})
            writer.sheets['Category_Spending'].insert_chart('D2', chart2)

        # Send file to user
        with open(filename, 'rb') as file:
            bot.send_document(
                chat_id,
                file,
                caption=f"Here's your {selected_type} history with charts from {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}"
            )

        # Clean up temporary file
        os.remove(filename)

    except Exception as e:
        logging.exception(str(e))
        bot.send_message(chat_id, f"An error occurred while generating the CSV: {str(e)}")