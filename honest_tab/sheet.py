import gspread

gclient = None
spreadsheet = None
user_sheet = None 
item_sheet = None 
order_sheet = None
admin_sheet = None

has_backend = False

try:
	gclient = gspread.service_account()
	spreadsheet = gclient.open("HonestTabData")
	user_sheet = spreadsheet.worksheet("users")
	item_sheet = spreadsheet.worksheet("items")
	order_sheet = spreadsheet.worksheet("orders")
	admin_sheet = spreadsheet.worksheet("admin")
	has_backend = True
except:
	print("Failed to load google sheets: running without backed")
