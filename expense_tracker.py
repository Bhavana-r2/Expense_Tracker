import sys
import gspread
from google.oauth2.service_account import Credentials
from PyQt5 import QtWidgets, QtCore
from datetime import datetime

# Step 1: Set up the scope and authenticate with the JSON credentials
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
gc = gspread.authorize(credentials)

# Step 2: Open the Google Sheet by its ID
sheet_id = ("1yOX-FSQN2NUArJgyYqMmhW6BKm"
            "Wis7GHqEoT3x_ozTM")  # Replace with your actual Google Sheet ID
expense_sheet = gc.open_by_key(sheet_id).sheet1  # First worksheet for expenses
petrol_sheet = gc.open_by_key(sheet_id).get_worksheet(1)  # Second worksheet for petrol details
budget_sheet = gc.open_by_key(sheet_id).get_worksheet(2)  # Third worksheet for budget values
budget_log_sheet = gc.open_by_key(sheet_id).get_worksheet(3)  # Fourth worksheet for budget log

# Initial budget setup if no rows exist in Google Sheets
budgets = {
    "Food": 1500,
    "Clothing": 1000,
    "Travel": 1000,
    "Meeting": 300
}


def add_expense(date, amount, category, description):
    try:
        # Log expense in the expense sheet
        expense_sheet.append_row([date, amount, category, description])

        # Decrement the budget in the log sheet if the category matches
        if category in budgets:
            budgets[category] -= float(amount)

            # Update the latest budget in the log sheet with the current date
            budget_log_sheet.append_row([datetime.now().strftime("%Y-%m-%d"), budgets['Food'], budgets['Clothing'], budgets['Travel'], budgets['Meeting']])

        return True
    except Exception as e:
        print("An error occurred while adding the expense:", e)
        return False


def add_petrol_details(date, litre, price, place):
    try:
        petrol_sheet.append_row([date, litre, price, place])
        return True
    except Exception as e:
        print("An error occurred while adding petrol details:", e)
        return False


def get_monthly_expenses(month, year):
    expenses_summary = []
    total_amount = 0
    try:
        records = expense_sheet.get_all_records()
        for record in records:
            date_str = str(record.get("date", ""))
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    if date_obj.month == month and date_obj.year == year:
                        expenses_summary.append(f"Amount: {record.get('amount')}, Category: {record.get('category')}, Description: {record.get('description')}")
                        total_amount += float(record.get("amount", 0))
                except ValueError:
                    print(f"Skipping row with invalid date format: {date_str}")
    except Exception as e:
        print("An error occurred while retrieving expenses:", e)
    return expenses_summary, total_amount


def get_budget_summary():
    try:
        rows = budget_log_sheet.get_all_values()
        if rows:
            latest_budget = rows[-1]
            budget_summary = [
                f"Food: ${float(latest_budget[1]):.2f}",
                f"Clothing: ${float(latest_budget[2]):.2f}",
                f"Travel: ${float(latest_budget[3]):.2f}",
                f"Meeting: ${float(latest_budget[4]):.2f}"
            ]
            # Update budgets dictionary with latest values
            budgets.update({
                "Food": float(latest_budget[1]),
                "Clothing": float(latest_budget[2]),
                "Travel": float(latest_budget[3]),
                "Meeting": float(latest_budget[4])
            })
            return budget_summary
    except Exception as e:
        print("An error occurred while retrieving the budget summary:", e)
        # Return predefined budgets if an error occurs
        return [f"{category}: ${amount:.2f}" for category, amount in budgets.items()]


def update_budget(new_budgets):
    global budgets
    budgets.update(new_budgets)

    try:
        # Log the updated budget values with the current date
        budget_log_sheet.append_row([datetime.now().strftime("%Y-%m-%d"), new_budgets['Food'], new_budgets['Clothing'], new_budgets['Travel'], new_budgets['Meeting']])
    except Exception as e:
        print("An error occurred while updating the budget in the sheet:", e)


class ExpenseTrackerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Personal Expense Tracker')
        layout = QtWidgets.QVBoxLayout()

        # Main Interface Buttons
        self.add_expense_button = QtWidgets.QPushButton('Add Expense', self)
        self.add_expense_button.clicked.connect(self.add_expense_interface)
        layout.addWidget(self.add_expense_button)

        self.view_expenses_button = QtWidgets.QPushButton('View Monthly Expenses', self)
        self.view_expenses_button.clicked.connect(self.view_monthly_expenses_interface)
        layout.addWidget(self.view_expenses_button)

        self.petrol_details_button = QtWidgets.QPushButton('Petrol Details', self)
        self.petrol_details_button.clicked.connect(self.petrol_details_interface)
        layout.addWidget(self.petrol_details_button)

        self.budget_button = QtWidgets.QPushButton('Budget', self)
        self.budget_button.clicked.connect(self.show_budget)
        layout.addWidget(self.budget_button)

        self.edit_budget_button = QtWidgets.QPushButton('Edit Budget', self)
        self.edit_budget_button.clicked.connect(self.edit_budget_interface)
        layout.addWidget(self.edit_budget_button)

        self.setLayout(layout)
        self.resize(300, 300)
        self.show()

    def add_expense_interface(self):
        self.expense_dialog = QtWidgets.QDialog(self)
        self.expense_dialog.setWindowTitle('Add Expense')
        layout = QtWidgets.QVBoxLayout()

        # Date picker
        self.date_input = QtWidgets.QDateEdit(self)
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QtCore.QDate.currentDate())

        self.amount_input = QtWidgets.QLineEdit(self)
        self.category_input = QtWidgets.QComboBox(self)
        self.category_input.addItems(["Food", "Clothing", "Meeting", "Travel", "Other"])
        self.description_input = QtWidgets.QLineEdit(self)

        layout.addWidget(QtWidgets.QLabel('Date:'))
        layout.addWidget(self.date_input)
        layout.addWidget(QtWidgets.QLabel('Amount:'))
        layout.addWidget(self.amount_input)
        layout.addWidget(QtWidgets.QLabel('Category:'))
        layout.addWidget(self.category_input)
        layout.addWidget(QtWidgets.QLabel('Description:'))
        layout.addWidget(self.description_input)

        self.add_button = QtWidgets.QPushButton('Add Expense', self)
        self.add_button.clicked.connect(self.add_expense_data)
        layout.addWidget(self.add_button)

        self.expense_dialog.setLayout(layout)
        self.expense_dialog.exec_()

    def add_expense_data(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        amount = self.amount_input.text()
        category = self.category_input.currentText()
        description = self.description_input.text()

        if add_expense(date, amount, category, description):
            QtWidgets.QMessageBox.information(self, 'Success', 'Expense added successfully!')
        else:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Failed to add expense.')

        self.expense_dialog.close()

    def view_monthly_expenses_interface(self):
        self.view_dialog = QtWidgets.QDialog(self)
        self.view_dialog.setWindowTitle('View Monthly Expenses')

        layout = QtWidgets.QVBoxLayout()
        self.month_input = QtWidgets.QSpinBox(self)
        self.month_input.setRange(1, 12)
        self.year_input = QtWidgets.QSpinBox(self)
        self.year_input.setRange(2000, 2100)

        layout.addWidget(QtWidgets.QLabel('Select Month:'))
        layout.addWidget(self.month_input)
        layout.addWidget(QtWidgets.QLabel('Select Year:'))
        layout.addWidget(self.year_input)

        self.view_button = QtWidgets.QPushButton('View Expenses', self)
        self.view_button.clicked.connect(self.view_expenses_data)
        layout.addWidget(self.view_button)

        self.expenses_display = QtWidgets.QPlainTextEdit(self)
        self.expenses_display.setReadOnly(True)
        layout.addWidget(self.expenses_display)

        self.view_dialog.setLayout(layout)
        self.view_dialog.exec_()

    def view_expenses_data(self):
        month = self.month_input.value()
        year = self.year_input.value()
        expenses, total = get_monthly_expenses(month, year)

        display_text = "\n".join(expenses) + f"\n\nTotal: ${total:.2f}"
        self.expenses_display.setPlainText(display_text)

    def petrol_details_interface(self):
        self.petrol_dialog = QtWidgets.QDialog(self)
        self.petrol_dialog.setWindowTitle('Add Petrol Details')
        layout = QtWidgets.QVBoxLayout()

        # Petrol date picker
        self.petrol_date_input = QtWidgets.QDateEdit(self)
        self.petrol_date_input.setCalendarPopup(True)
        self.petrol_date_input.setDate(QtCore.QDate.currentDate())

        self.litre_radio = QtWidgets.QRadioButton('Litres', self)
        self.price_radio = QtWidgets.QRadioButton('Price', self)
        self.place_radio = QtWidgets.QRadioButton('Place', self)

        layout.addWidget(self.petrol_date_input)
        layout.addWidget(self.litre_radio)
        layout.addWidget(self.price_radio)
        layout.addWidget(self.place_radio)

        self.add_petrol_button = QtWidgets.QPushButton('Add Petrol Detail', self)
        self.add_petrol_button.clicked.connect(self.add_petrol_data)
        layout.addWidget(self.add_petrol_button)

        self.petrol_dialog.setLayout(layout)
        self.petrol_dialog.exec_()

    def show_budget(self):
        budget_summary = get_budget_summary()
        budget_details = "\n".join(budget_summary)
        QtWidgets.QMessageBox.information(self, 'Budget Summary', budget_details)

    def edit_budget_interface(self):
        self.edit_dialog = QtWidgets.QDialog(self)
        self.edit_dialog.setWindowTitle('Edit Budget')
        layout = QtWidgets.QVBoxLayout()

        self.food_input = QtWidgets.QLineEdit(self)
        self.food_input.setPlaceholderText(f"Current: ${budgets['Food']:.2f}")

        self.clothing_input = QtWidgets.QLineEdit(self)
        self.clothing_input.setPlaceholderText(f"Current: ${budgets['Clothing']:.2f}")

        self.travel_input = QtWidgets.QLineEdit(self)
        self.travel_input.setPlaceholderText(f"Current: ${budgets['Travel']:.2f}")

        self.meeting_input = QtWidgets.QLineEdit(self)
        self.meeting_input.setPlaceholderText(f"Current: ${budgets['Meeting']:.2f}")

        layout.addWidget(QtWidgets.QLabel('Food Budget:'))
        layout.addWidget(self.food_input)
        layout.addWidget(QtWidgets.QLabel('Clothing Budget:'))
        layout.addWidget(self.clothing_input)
        layout.addWidget(QtWidgets.QLabel('Travel Budget:'))
        layout.addWidget(self.travel_input)
        layout.addWidget(QtWidgets.QLabel('Meeting Budget:'))
        layout.addWidget(self.meeting_input)

        self.update_button = QtWidgets.QPushButton('Update Budget', self)
        self.update_button.clicked.connect(self.update_budget_data)
        layout.addWidget(self.update_button)

        self.edit_dialog.setLayout(layout)
        self.edit_dialog.exec_()

    def update_budget_data(self):
        new_budgets = {
            "Food": float(self.food_input.text() or budgets['Food']),
            "Clothing": float(self.clothing_input.text() or budgets['Clothing']),
            "Travel": float(self.travel_input.text() or budgets['Travel']),
            "Meeting": float(self.meeting_input.text() or budgets['Meeting']),
        }
        update_budget(new_budgets)
        QtWidgets.QMessageBox.information(self, 'Success', 'Budget updated successfully!')
        self.edit_dialog.close()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = ExpenseTrackerApp()
    sys.exit(app.exec_())
