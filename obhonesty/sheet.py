from pathlib import Path

import gspread

GSPREAD_SERVICE_ACCOUNT_CREDENTIALS_PATH = \
	Path(".credentials/service_account.json")

gclient = gspread.service_account(GSPREAD_SERVICE_ACCOUNT_CREDENTIALS_PATH)
spreadsheet = gclient.open("Test - OBHonestyData")
user_sheet = spreadsheet.worksheet("users")
item_sheet = spreadsheet.worksheet("items")
order_sheet = spreadsheet.worksheet("orders")
admin_sheet = spreadsheet.worksheet("admin")
