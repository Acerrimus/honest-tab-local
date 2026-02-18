import reflex as rx
from datetime import datetime, timedelta
from sqlalchemy import select

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
  # these must default to False otherwise the app crashes on startup
  current_guest: bool = False
  active_tab: bool = False
  prepaid_dinners_quantity: int

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

class Admin(rx.Model, table=True):
  key: str
  value: str

class Meal(rx.Model, table=True):
  meal_id: str
  order_id: str
  user_nick_name: str
  receiver: str
  order_time: datetime
  meal_type: str
  diet: str
  allergies: str
  volunteer: bool
  served: bool

  @classmethod
  def select_todays_meals(cls, meal_type: str | None = None):
      now = datetime.now()
      today = now.date()
      start = datetime.combine(today, datetime.min.time())
      end = start + timedelta(days=1)

      return select(cls).where(
              cls.meal_type == meal_type,
              cls.order_time >= start,
              cls.order_time < end
          ) if meal_type is not None else select(cls).where(
              cls.order_time >= start,
              cls.order_time < end
          )
  
  @classmethod
  def select_todays_breakfast_meals(cls):
    return cls.select_todays_meals("breakfast")
  
  @classmethod
  def select_todays_dinner_meals(cls):
    return cls.select_todays_meals("dinner")