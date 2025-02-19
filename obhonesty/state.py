
from datetime import datetime
from typing import Any, Dict, List, Optional

import reflex as rx

from obhonesty.aux import short_uid
from obhonesty.user import User
from obhonesty.item import Item
from obhonesty.order import Order
from obhonesty.sheet import user_sheet, item_sheet, order_sheet, admin_sheet

class State(rx.State):
  """The app state."""
  admin_data: Dict[str, Any]
  users: List[User]
  items: Dict[str, Item]
  current_user: Optional[User]
  new_nick_name: str
  custom_item_price: str
  orders: List[Order]

  @rx.event
  def reload_sheet_data(self):
    print("Reloading sheet data")
    user_data = user_sheet.get_all_records(expected_headers=[
      'nick_name', 'first_name', 'last_name', 'phone_number', 'email',
      'address', 'volunteer', 'away', 'diet', 'allergies', 'owes'
    ]) 
    item_data = item_sheet.get_all_records(expected_headers=[
      'name', 'price', 'description', 'tax_category'
    ])
    order_data = order_sheet.get_all_records(expected_headers=[
      'order_id', 'user', 'time', 'item', 'quantity', 'price', 'total',
      'diet', 'allergies', 'served', 'tax_category', 'comment'
    ])
    self.admin_data = admin_sheet.get_all_records()[0]
    self.users = [
      User.from_dict(x) for x in user_data if x['nick_name'] != ''
    ]
    self.items = {
      x['name'] : Item.from_dict(x) for x in item_data if x['name'] != ''
    }
    self.orders = [
      Order.from_dict(x) for x in order_data
    ]
    self.users.sort(key=lambda x: x.nick_name)

  @rx.event
  def redirect_to_user_page(self, user: User):
    self.current_user = user
    return rx.redirect("/user")
  
  @rx.event
  def redirect_to_admin_user_page(self, user: User):
    self.current_user = user
    return rx.redirect("/admin/user")

  @rx.event
  def redirect_no_user(self):
    if self.current_user is None:
      return rx.redirect("/")
    
  @rx.event
  def order_item(self, form_data: dict):
    item = self.items[form_data['item_name']]
    try:
      quantity = float(form_data['quantity'])
    except:
      return rx.toast.error("Failed to register. Quantity must be a number")
    order_sheet.append_row([
      str(short_uid()), 
      self.current_user.nick_name,
      str(datetime.now()),
      item.name,
      quantity,
      item.price,
      quantity * item.price,
      "", "", "", "",
      item.tax_category,
      ""
    ], table_range="A1")
    return rx.toast.info(
      f"'{item.name}' registered succesfully. Thank you!",
      position="bottom-center"
    )
  
  @rx.event
  def order_custom_item(self, form_data: dict):
    item_name = form_data['custom_item_name']
    order_sheet.append_row([
      str(short_uid()), 
      self.current_user.nick_name,
      str(datetime.now()),
      item_name,
      1.0,
      float(form_data['custom_item_price']),
      float(form_data['custom_item_price']),
      "", "", "", "",
      form_data['tax_category'],
      form_data['custom_item_description']
    ], table_range="A1")
    return rx.redirect("/user")
  
  @rx.event
  def order_dinner(self, form_data: dict):
    first_name = form_data['first_name'].upper().strip()
    last_name = form_data['last_name'].upper().strip()
    receiver = f"{first_name} {last_name}" 
    if receiver in [order.receiver for order in self.dinner_signups]:
      return rx.toast.error(
        "This person is already signed up, "
        "please provide different name if you want to sign up another person."
      )
    row = [
      str(short_uid()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Dinner sign-up",
      1,
      self.admin_data['dinner_price'],
      self.admin_data['dinner_price'],
      receiver,
      form_data['diet'],
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ]
    order_sheet.append_row(row, table_range="A1")
    return rx.redirect("/user")
  
  @rx.event
  def order_dinner_late(self, form_data: dict): 
    row = [
      str(short_uid()), 
      form_data['nick_name'],
      str(datetime.now()),
      "Dinner sign-up",
      1,
      self.admin_data['dinner_price'],
      self.admin_data['dinner_price'],
      form_data['full_name'].upper().trim(),
      form_data['diet'],
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ]
    order_sheet.append_row(row, table_range="A1")
    return rx.redirect("/admin/dinner")

  @rx.event
  def order_breakfast(self, form_data: dict):
    first_name = form_data['first_name'].upper().strip()
    last_name = form_data['last_name'].upper().strip()
    receiver = f"{first_name} {last_name}" 
    if not form_data['menu_item'].lower().startswith("packed lunch") and receiver in [
      order.receiver for order in self.breakfast_signups
      if not order.diet.lower().startswith("packed lunch")
    ]:
      return rx.toast.error(
        "This person is already signed up, "
        "please provide different name if you want to sign up another person."
      )
    menu_item = form_data['menu_item']
    key = f"{menu_item}_price"
    price = self.admin_data[key] if not self.current_user.volunteer else 0.0
    row = [
      str(short_uid()), 
      self.current_user.nick_name,
      str(datetime.now()),
      "Breakfast sign-up",
      1,
      price,
      price,
      receiver,
      menu_item,
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ]
    order_sheet.append_row(row, table_range="A1")
    return rx.redirect("/user")
  
  @rx.event
  def submit_signup(self, form_data: dict):
    user_sheet.append_row(list(form_data.values()), table_range="A1")
    return rx.redirect("/")
  
  @rx.var(cache=False)
  def current_user_orders(self) -> List[Order]:
    filtered: List[Order] = []
    for order in self.orders:
      if order.user_nick_name == self.current_user.nick_name:
        order_copy = order.copy()
        try:
          order_copy.time = datetime.fromisoformat(order.time).strftime(
            "%Y-%m-%d, %H:%M:%S"
          )
        except:
          pass
        filtered.append(order_copy)
    filtered.sort(key=lambda x: x.time, reverse=True)
    return filtered
  
  @rx.var(cache=False)
  def no_user(self) -> bool:
    return self.current_user is None

  @rx.var(cache=False)
  def invalid_new_user_name(self) -> bool:
    return self.new_nick_name in [x.nick_name for x in self.users]
  
  @rx.var(cache=False)
  def invalid_custom_item_price(self) -> bool:
    try:
      # Convert to float and check decimals
      float_val = float(self.custom_item_price)
      # Optionally check decimal places
      if len(str(float_val).split('.')[-2]) <= 2:  # For 2 decimal places
        return False
      return True
    except ValueError:
      return True 
  
  @rx.var(cache=False)
  def dinner_signup_available(self) -> int:
    try:
      deadline = datetime.strptime(self.admin_data['dinner_signup_deadline'], "%H:%M")
    except:
      deadline = datetime.strptime("22:59", "%H:%M")
    now = datetime.now()
    deadline_minutes = deadline.hour * 60 + deadline.minute
    now_minutes = now.hour * 60 + now.minute
    return now_minutes < deadline_minutes
  
  @rx.var(cache=False)
  def breakfast_signup_available(self) -> bool:
    try:
      deadline = datetime.strptime(self.admin_data['breakfast_signup_deadline'], "%H:%M")
    except:
      deadline = datetime.strptime("22:59", "%H:%M")
    now = datetime.now()
    deadline_minutes = deadline.hour * 60 + deadline.minute
    now_minutes = now.hour * 60 + now.minute
    return now_minutes < deadline_minutes
  
  @rx.var(cache=False)
  def tax_categories(self) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for order in self.orders:
      if not order.tax_category in result:
        result[order.tax_category] = 0.0
      result[order.tax_category] += order.price
    return result

  @rx.var(cache=False)
  def breakfast_signups(self) -> List[Order]:
    signups: List[Order] = []
    for order in self.orders:
      try:
        order_date = datetime.fromisoformat(order.time).date()
      except:
        pass
      if order.item == "Breakfast sign-up" and \
          order_date == datetime.today().date():
        order_alt = order.copy()
        order_alt.time = datetime.fromisoformat(order.time).strftime("%H:%M:%S")
        signups.append(order_alt)
    signups.sort(key=lambda x: x.time, reverse=True)
    return signups
  
  @rx.var(cache=False)
  def dinner_signups(self) -> List[Order]:
    signups: List[Order] = []
    for order in self.orders:
      try:
        order_date = datetime.fromisoformat(order.time).date()
      except:
        pass
      if order.item == "Dinner sign-up" and \
          order_date == datetime.today().date():
        signups.append(order)
    for user in self.users:
      if user.volunteer:
        signups.append(Order(order_id="",
          user_nick_name=user.nick_name, time="",
          item="Dinner sign-up (volunteer)",
          quantity=1.0, price=0.0, total=0.0,
          receiver=f"{user.first_name} {user.last_name}", diet=user.diet,
          allergies=user.allergies, served="", tax_category="",
          comment="yes"
        ))
    signups.sort(key=lambda x: x.receiver)    
    signups.sort(key=lambda x: x.diet)    
    signups.sort(key=lambda x: x.comment)    
    return signups
  
  @rx.var(cache=False)
  def dinner_count(self) -> int:
    return len(self.dinner_signups)
  
  @rx.var(cache=False)
  def dinner_count_vegan(self) -> int:
    count = 0
    for order in self.dinner_signups:
      if order.diet == "Vegan":
        count += 1
    return count
  
  @rx.var(cache=False)
  def dinner_count_vegetarian(self) -> int:
    count = 0
    for order in self.dinner_signups:
      if order.diet == "Vegetarian":
        count += 1
    return count
  
  @rx.var(cache=False)
  def dinner_count_meat(self) -> int:
    count = 0
    for order in self.dinner_signups:
      if order.diet == "Meat":
        count += 1
    return count
  
  @rx.var(cache=False)
  def get_user_debt(self) -> float:
    return sum([order.total for order in self.current_user_orders])
  
  @rx.var(cache=False)
  def get_all_nick_names(self) -> List[str]:
    return [user.nick_name for user in self.users]
