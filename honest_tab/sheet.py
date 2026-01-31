from pathlib import Path
import gspread

has_backend = False

try:
	GSPREAD_SERVICE_ACCOUNT_CREDENTIALS_PATH = \
		Path(".credentials/service_account.json")

	gclient = gspread.service_account(GSPREAD_SERVICE_ACCOUNT_CREDENTIALS_PATH)
	spreadsheet = gclient.open("Test - OBHonestyData")
	user_sheet = spreadsheet.worksheet("users")
	item_sheet = spreadsheet.worksheet("items")
	order_sheet = spreadsheet.worksheet("orders")
	admin_sheet = spreadsheet.worksheet("admin")

	has_backend = True
except:
	print("Failed to load google sheets: running without backed")