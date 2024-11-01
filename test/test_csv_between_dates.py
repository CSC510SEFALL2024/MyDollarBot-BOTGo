import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from code.csv_between_dates import run, post_type_selection, get_start_date, get_end_date, generate_csv  # Adjust this to match your actual module path

class TestBotFunctions(unittest.TestCase):
    
    def setUp(self):
        self.bot = MagicMock()
        self.message = MagicMock()
        self.message.chat.id = 12345  # Example chat ID

    @patch('code.csv_between_dates.helper.getIncomeOrExpense')
    def test_run_function(self, mock_getIncomeOrExpense):
        # Mock the helper function to return expected options
        mock_getIncomeOrExpense.return_value = {'income': 'Income', 'expense': 'Expense'}
        
        # Call the function
        run(self.message, self.bot)
        
        # Capture the actual markup used in the reply_to call
        actual_reply_markup = self.bot.reply_to.call_args[1]['reply_markup']
        
        # Check that reply_to was called once with expected message and reply markup
        self.bot.reply_to.assert_called_once_with(self.message, 'Select Income or Expense', reply_markup=actual_reply_markup)


    @patch('code.csv_between_dates.post_type_selection')  # Adjust based on where post_type_selection is located
    def test_post_type_selection_valid(self, mock_post_type_selection):
        self.message.text = 'Income'
        post_type_selection(self.message, self.bot)
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "Please enter the start date in yyyy-mm-dd format.")

    def test_get_start_date_invalid_format(self):
        self.message.text = '2023/01/01'  # Invalid date format
        get_start_date(self.message, self.bot, 'Income')
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "Invalid date format. Please enter the start date in yyyy-mm-dd format.")

    def test_get_start_date_valid(self):
        self.message.text = '2023-01-01'  # Valid date format
        get_start_date(self.message, self.bot, 'Expense')
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "Please enter the end date in yyyy-mm-dd format.")

    def test_get_end_date_invalid_format(self):
        start_date_obj = datetime.strptime('2023-01-01', "%Y-%m-%d")
        self.message.text = '01-01-2023'  # Invalid end date format
        get_end_date(self.message, self.bot, 'Income', start_date_obj)
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "Invalid date format. Please enter the end date in yyyy-mm-dd format.")

    def test_get_end_date_start_after_end(self):
        start_date_obj = datetime.strptime('2023-01-01', "%Y-%m-%d")
        self.message.text = '2022-12-31'  # End date before start date
        get_end_date(self.message, self.bot, 'Expense', start_date_obj)
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "End date must be after the start date. Please enter the end date again.")

    @patch('code.csv_between_dates.helper.getUserHistory')  # Adjust based on where helper is located
    def test_generate_csv_no_records(self, mock_getUserHistory):
        start_date_obj = datetime.strptime('2023-01-01', "%Y-%m-%d")
        end_date_obj = datetime.strptime('2023-01-31', "%Y-%m-%d")
        
        # Mocking an empty return value to simulate no user history
        mock_getUserHistory.return_value = []
        
        # Run the function
        generate_csv(self.message.chat.id, self.bot, 'Income', mock_getUserHistory.return_value, start_date_obj, end_date_obj)

        # Ensure send_message was called with the specific message when no records are found
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "No records found within the selected date range!")

    @patch('code.csv_between_dates.post_type_selection')
    def test_post_type_selection_message(self, mock_post_type_selection):
        # Simulate a valid selection
        self.message.text = 'Income'
        
        # Call the mocked function
        post_type_selection(self.message, self.bot)

        # Assert that the bot sends a message prompting for the start date
        self.bot.send_message.assert_called_once_with(self.message.chat.id, "Please enter the start date in yyyy-mm-dd format.")


    def test_get_start_date_invalid_format(self):
        """Test that an invalid date format prompts an error message."""
        # Simulate an invalid date input
        self.message.text = '01/01/2023'  # Invalid format
        
        # Call the get_start_date function
        get_start_date(self.message, self.bot, 'Income')
        
        # Check that bot responds with an error message about invalid format
        self.bot.send_message.assert_called_once_with(
            self.message.chat.id, "Invalid date format. Please enter the start date in yyyy-mm-dd format."
        )

if __name__ == '__main__':
    unittest.main()
