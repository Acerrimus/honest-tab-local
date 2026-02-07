import reflex as rx

# These classes specify the table info for the SQL database, storing google sheets data offline.
# They must be updated if any new columns are added.

# synced is a prop only in the sqlite db.
class User(rx.Model, table=True):
  nick_name: str
  first_name: str
  last_name: str
  email: str
  phone_number: str
  volunteer: bool
  away: bool
  diet: str
  allergies: str
  synced: bool

class Order(rx.Model, table=True):
  order_id: str
  user_nick_name: str
  time: str
  item: str
  quantity: float
  price: float
  total: float
  receiver: str
  diet: str
  allergies: str
  served: str
  tax_category: str
  comment: str
  paid: str | None
  paid_time: str | None
  method: str | None 
  checkout_staff: str | None
  synced: bool

class Item(rx.Model, table=True):
  name: str
  price: float
  description: str
  tax_category: str