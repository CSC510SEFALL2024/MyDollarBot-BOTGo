import re
import json
import os
from datetime import datetime

choices = ['Date', 'Category', 'Cost']
plot = ['Bar with budget', 'Pie', 'Bar without budget']
spend_display_option = ['Day', 'Month']
spend_categories = ['Food', 'Groceries', 'Utilities',
                    'Transport', 'Shopping', 'Miscellaneous']
spend_estimate_option = ['Next day', 'Next month']
update_options = {
    'continue': 'Continue',
    'exit': 'Exit'
}

budget_options = {
    'update': 'Add/Update',
    'view': 'View',
    'max_spend': 'Transaction Max Spend Limit',
    'delete': 'Delete'
}

budget_types = {
    'overall': 'Overall Budget',
    'category': 'Category-Wise Budget',
}

data_format = {
    'data': [],
    'income_data': [],
    'budget': {
        'overall': None,
        'category': None,
        'max_per_txn_spend': None
    },
    'max_expenditure_limits': [
        {
            'limit': None,          # Maximum spend allowed within time frame
            'time_frame': None,      # Time period (e.g., "Oct-2023")
            'current_spending': 0    # Accumulated spending within the time frame
        }
    ]
}


income_or_expense_options = {
    'income': 'Income',
    'expense': 'Expense'
}

category_options = {
    'add': 'Add',
    'delete': 'Delete',
    'view': 'Show Categories'
}

# set of implemented commands and their description
commands = {
    'menu': 'Display this menu',
    'add_expense': 'Record/Add a new spending',
    'add_recurring': 'Add a new recurring expense for future months',
    'display': 'Show sum of expenditure for the current day/month',
    'estimate': 'Show an estimate of expenditure for the next day/month',
    'history': 'Display spending history',
    'delete': 'Clear/Erase all your records',
    'edit': 'Edit/Change spending details',
    'budget': 'Add/Update/View/Delete budget',
    'category': 'Add/Delete/Show custom categories',
    'extract': 'Extract data into CSV',
    'sendEmail': 'Email CSV to user',
    'receipt': 'Show the receipt for the day',
    'upload':'Upload CSV file for bulk insert',
    'add_income': 'Add a new income',
    'DisplayCurrency': 'Display total expenditure in a currency of your choice',
    'chat': 'Chat with the bot',
    'pdf': 'Generate a pdf for Income or History',
    'savings_tracker': 'tracks savings',
    'csv':  'Generate a csv file for Income or Expenses',
    'scan_receipt': 'Scan a receipt using AI to upload transactions',
    'csv_between_dates': 'Generate a csv file for Income or Expenses between user set dates.'
}

dateFormat = '%d-%b-%Y'
timeFormat = '%H:%M'
monthFormat = '%b-%Y'


# function to load .json expense record data
def read_json():
    try:
        if not os.path.exists('expense_record.json'):
            with open('expense_record.json', 'w') as json_file:
                json_file.write('{}')
            return json.dumps('{}')
        elif os.stat('expense_record.json').st_size != 0:
            with open('expense_record.json') as expense_record:
                expense_record_data = json.load(expense_record)
            return expense_record_data

    except FileNotFoundError:
        print("---------NO RECORDS FOUND---------")


def write_json(user_list):
    try:
        with open('expense_record.json', 'w') as json_file:
            json.dump(user_list, json_file, ensure_ascii=False, indent=4)
    except FileNotFoundError:
        print('Sorry, the data file could not be found.')


def validate_entered_amount(amount_entered):
    if amount_entered is None:
        return 0
    if re.match("^[1-9][0-9]{0,14}\\.[0-9]*$", amount_entered) or re.match("^[1-9][0-9]{0,14}$", amount_entered):
        amount = round(float(amount_entered), 2)
        if amount > 0:
            return str(amount)
    return 0


def validate_entered_duration(duration_entered):
    if duration_entered is None:
        return 0
    if re.match("^[1-9][0-9]{0,14}", duration_entered):
        duration = int(duration_entered)
        if duration > 0:
            return str(duration)
    return 0


def validate_transaction_limit(chat_id, amount_value, bot):
    if isMaxTransactionLimitAvailable(chat_id):
        maxLimit = round(float(getMaxTransactionLimit(chat_id)), 2)
        if round(float(amount_value), 2) >= maxLimit:
            bot.send_message(
                chat_id, 'Warning! You went over your transaction spend limit')


def getUserExpenseHistory(chat_id):
    data = getUserData(chat_id)
    if data is not None:
        return data['data']
    return None


def getUserIncomeHistory(chat_id):
    data = getUserData(chat_id)
    if data is not None:
        if 'income_data' in data:
            return data['income_data']
    return None


def getUserData(chat_id):
    user_list = read_json()
    if user_list is None:
        return None
    if (str(chat_id) in user_list):
        return user_list[str(chat_id)]
    return None


def throw_exception(e, message, bot, logging):
    logging.exception(str(e))
    bot.reply_to(message, 'Oh no! ' + str(e))


def createNewUserRecord():
    return data_format


def getOverallBudget(chatId):
    data = getUserData(chatId)
    if data is None:
        return None
    return data['budget']['overall']


def getCategoryBudget(chatId):
    data = getUserData(chatId)
    if data is None:
        return None
    return data['budget']['category']


def getMaxTransactionLimit(chatId):
    data = getUserData(chatId)
    if data is None or 'budget' not in data or 'max_per_txn_spend' not in data['budget']:
        return None
    return data['budget']['max_per_txn_spend']


def getCategoryBudgetByCategory(chatId, cat):
    if not isCategoryBudgetByCategoryAvailable(chatId, cat):
        return None
    data = getCategoryBudget(chatId)
    return data[cat]


def canAddBudget(chatId):
    return (getOverallBudget(chatId) is None) and (getCategoryBudget(chatId) is None)


def isOverallBudgetAvailable(chatId):
    return getOverallBudget(chatId) is not None


def isCategoryBudgetAvailable(chatId):
    return getCategoryBudget(chatId) is not None


def isCategoryBudgetByCategoryAvailable(chatId, cat):
    data = getCategoryBudget(chatId)
    if data is None:
        return False
    return cat in data.keys()


def isMaxTransactionLimitAvailable(chatId):
    return getMaxTransactionLimit(chatId) is not None


def display_remaining_budget(message, bot, cat):
    chat_id = message.chat.id
    if isOverallBudgetAvailable(chat_id):
        display_remaining_overall_budget(message, bot)
    elif isCategoryBudgetByCategoryAvailable(chat_id, cat):
        display_remaining_category_budget(message, bot, cat)


def display_remaining_overall_budget(message, bot):
    print('here')
    chat_id = message.chat.id
    remaining_budget = calculateRemainingOverallBudget(chat_id)
    print("here", remaining_budget)
    if remaining_budget >= 0:
        msg = '\nRemaining Overall Budget is $' + str(remaining_budget)
    else:
        msg = '\nBudget Exceded!\nExpenditure exceeds the budget by $' + \
              str(remaining_budget)[1:]
    bot.send_message(chat_id, msg)


def calculateRemainingOverallBudget(chat_id):
    budget = getOverallBudget(chat_id)
    history = getUserExpenseHistory(chat_id)
    query = datetime.now().today().strftime(getMonthFormat())
    queryResult = [value for index, value in enumerate(
        history) if str(query) in value]

    return float(budget) - calculate_total_spendings(queryResult)


def calculate_total_spendings(queryResult):
    total = 0

    for row in queryResult:
        s = row.split(',')
        total = total + float(s[2])
    return total


def display_remaining_category_budget(message, bot, cat):
    chat_id = message.chat.id
    remaining_budget = calculateRemainingCategoryBudget(chat_id, cat)
    if remaining_budget >= 0:
        msg = '\nRemaining Budget for ' + cat + ' is $' + str(remaining_budget)
    else:
        msg = '\nBudget for ' + cat + \
              ' Exceded!\nExpenditure exceeds the budget by $' + \
              str(abs(remaining_budget))
    bot.send_message(chat_id, msg)


def calculateRemainingCategoryBudget(chat_id, cat):
    budget = getCategoryBudgetByCategory(chat_id, cat)
    history = getUserExpenseHistory(chat_id)
    query = datetime.now().today().strftime(getMonthFormat())
    queryResult = [value for index, value in enumerate(
        history) if str(query) in value]

    return float(budget) - calculate_total_spendings_for_category(queryResult, cat)


def calculate_total_spendings_for_category(queryResult, cat):
    total = 0

    for row in queryResult:
        s = row.split(',')
        if cat == s[1]:
            total = total + float(s[2])
    return total


def getSpendCategories():
    with open("categories.txt", "r") as tf:
        spend_categories = tf.read().split(',')
    return spend_categories


def getplot():
    return plot


def getSpendDisplayOptions():
    return spend_display_option


def getSpendEstimateOptions():
    return spend_estimate_option


def getCommands():
    return commands


def getDateFormat():
    return dateFormat


def getTimeFormat():
    return timeFormat


def getMonthFormat():
    return monthFormat


def getChoices():
    return choices


def getBudgetOptions():
    return budget_options


def getBudgetTypes():
    return budget_types


def getUpdateOptions():
    return update_options


def getCategoryOptions():
    return category_options


def getIncomeCategories():
    with open("income_categories.txt", "r") as tf:
        income_categories = tf.read().split(',')
    return income_categories


def getCategories(selectedType):
    if selectedType == "Income":
        income_categories = getIncomeCategories()
        return income_categories
    else:
        spend_categories = getSpendCategories()
        return spend_categories


def getIncomeOrExpense():
    return income_or_expense_options


def getUserHistory(chat_id, selectedType):
    if selectedType == "Income":
        return getUserIncomeHistory(chat_id)
    else:
        return getUserExpenseHistory(chat_id)


def set_max_expenditure_limit(chat_id, limit, time_frame):
    data = getUserData(chat_id)
    existing_spending = calculate_spending_for_time_frame(data['data'], time_frame)

    new_limit = {
        "limit": limit,
        "time_frame": time_frame,
        "current_spending": existing_spending
    }
    # Append the new limit entry to the list
    data['max_expenditure_limits'].append(new_limit)
    write_json(data)


def check_spending_limit(chat_id, amount, bot, expense_date):
    data = getUserData(chat_id)
    for limit_data in data.get('max_expenditure_limits', []):
        if not limit_data['limit']:
            continue  # Skip if no limit is set

        # Parse the time frame start and end dates
        start_date_str, end_date_str = limit_data['time_frame'].split(" to ")
        start_date = datetime.strptime(start_date_str, '%d-%b-%Y')
        end_date = datetime.strptime(end_date_str, '%d-%b-%Y')

        # Only add the amount if the expense_date is within the time frame
        if start_date <= expense_date <= end_date:
            limit = float(limit_data['limit'])
            limit_data['current_spending'] += float(amount)
            current_spending = limit_data['current_spending']

            percentage_spent = (current_spending / limit) * 100

            if percentage_spent >= 100:
                bot.send_message(chat_id, f"⚠️ You've reached 100% of your {limit_data['time_frame']} spending limit!")
            elif percentage_spent >= 75:
                bot.send_message(chat_id, f"⚠️ You've reached 75% of your {limit_data['time_frame']} spending limit!")
            elif percentage_spent >= 50:
                bot.send_message(chat_id, f"⚠️ You've reached 50% of your {limit_data['time_frame']} spending limit!")

    write_json(data)


def calculate_spending_for_time_frame(expenses, time_frame):
    total_spending = 0
    for entry in expenses:
        date_str, category, amount = entry.split(',')
        expense_date = datetime.strptime(date_str, '%d-%b-%Y %H:%M')
        
        # Adjust the following condition to match your time frame format
        if matches_time_frame(expense_date, time_frame):
            total_spending += float(amount)
    
    return total_spending

def matches_time_frame(expense_date, time_frame):
    # Parse the time_frame string into a date object
    frame_date = datetime.strptime(time_frame, '%d-%b-%Y')  # Assumes '02-Oct-2024' format
    
    # Check if expense_date matches frame_date exactly (year, month, day)
    return (
        expense_date.year == frame_date.year and
        expense_date.month == frame_date.month and
        expense_date.day == frame_date.day
    )
