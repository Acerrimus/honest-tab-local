
from datetime import datetime
import asyncio
from typing import Any, Dict, List, Optional

import reflex as rx

from honest_tab.aux import short_uid, str_cmp
from honest_tab.constants import Diet, true_values
from honest_tab.user import User
from honest_tab.item import Item
from honest_tab.order import Order
from honest_tab.sheet import user_sheet, item_sheet, order_sheet, admin_sheet, has_backend

class State(rx.State):
  """The app state."""
  admin_data: Dict[str, Any]
  users: List[User]
  items: Dict[str, Item]
  current_user: Optional[User]
  new_nick_name: str
  custom_item_price: str
  orders: List[Order]
  cancel_redirect: bool

  @rx.event
  def cancel_timeout(self):
    self.cancel_redirect = True
  
  @rx.event(background=True)
  async def on_user_login(self):
    async with self:
      self.cancel_redirect = False
    await asyncio.sleep(120)
    if not self.cancel_redirect:
      yield rx.redirect("/")

  @rx.event(background=True)
  async def reload_sheet_data(self):
    async with self:
      self.cancel_redirect = True
      user_data = [] if user_sheet is None else user_sheet.get_all_records(expected_headers=[
        'nick_name', 'first_name', 'last_name', 'phone_number', 'email',
        'diet', 'allergies', 'volunteer', 'away', 'owes'
      ])
      item_data = [] if item_sheet is None else item_sheet.get_all_records(expected_headers=[
        'name', 'price', 'description', 'tax_category'
      ])
      order_data = [] if item_sheet is None else order_sheet.get_all_records(expected_headers=[
        'order_id', 'user', 'time', 'item', 'quantity', 'price', 'total',
        'diet', 'allergies', 'served', 'tax_category', 'comment'
      ])
      self.admin_data = {} if admin_sheet is None else admin_sheet.get_all_records()[0]
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
    if has_backend: yield rx.toast.info("Data reloaded", duration=2000)
    else: yield rx.toast.warning("No backend: no changes were recorded", duration=3000)

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
    if order_sheet:
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
    else: return rx.toast.info("No backend")
  
  @rx.event
  def order_custom_item(self, form_data: dict):
    item_name = form_data['custom_item_name']
    if order_sheet:
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
    if order_sheet:
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
      form_data['full_name'].upper().strip(),
      form_data['diet'],
      form_data['allergies'],
      "",
      "Food and beverage non-alcoholic",
      ""
    ]
    if order_sheet:
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
    if order_sheet: order_sheet.append_row(row, table_range="A1")
    return rx.redirect("/user")
  
  @rx.event
  def submit_signup(self, form_data: dict):
    if user_sheet: user_sheet.append_row(list(form_data.values()), table_range="A1")
    return rx.redirect("/")
  
  @rx.var(cache=False)
  def current_user_orders(self) -> List[Order]:
    filtered: List[Order] = []
    for order in self.orders:
      if self.current_user and order.user_nick_name == self.current_user.nick_name:
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
          except BaseException:
              continue
          
          if order.item == "Breakfast sign-up" and order_date == datetime.today().date():
              order_alt = order.copy()
              try:
                  order_alt.time = datetime.fromisoformat(
                      order.time).strftime("%H:%M:%S")
              except:
                  pass
              signups.append(order_alt)
      signups.sort(key=lambda x: x.time, reverse=True)
      return signups
  
  @rx.var(cache=False)
  def dinner_signups(self) -> List[Order]:
      signups: List[Order] = []
      for order in self.orders:
          try:
              order_date = datetime.fromisoformat(order.time).date()
          except BaseException:
              continue
              
          if order.item == "Dinner sign-up" and order_date == datetime.today().date():
              signups.append(order)
              
      for user in self.users:
          if user.volunteer:
              full_name = f"{user.first_name.upper()} {user.last_name.upper()}"
              signups.append(
                  Order(
                      order_id="",
                      user_nick_name=user.nick_name,
                      time="",
                      item="Dinner sign-up (volunteer)",
                      quantity=1.0,
                      price=0.0,
                      total=0.0,
                      receiver=full_name,
                      diet=user.diet,
                      allergies=user.allergies,
                      served=False,
                      tax_category="",
                      comment=true_values[0]))
      signups.sort(key=lambda x: x.receiver)
      signups.sort(key=lambda x: x.diet)
      signups.sort(key=lambda x: x.comment)
      return signups

  

  @rx.event(background=True)
  async def set_served(self, order_id: str, value: bool):
      # Calculate string value for sheet
      new_str = "TRUE" if value else "FALSE"

      # 1. Update Backend (Google Sheet)
      if order_sheet and order_id:
          try:
              cell = order_sheet.find(order_id)
              try:
                  header_cell = order_sheet.find("served", in_row=1)
                  col_number = header_cell.col
                  if cell:
                      order_sheet.update_cell(cell.row, col_number, new_str)
              except Exception as e:
                  print(f"Error finding column header: {e}")
          except Exception as e:
              print(f"Failed to update sheet: {e}")
      else:
          print("Could not find order")

      # 2. Update Local State (UI)
      async with self:
          for order in self.orders:
              if order.order_id == order_id:
                  order.served = new_str
                  break
          self.orders = self.orders



# ====== GET TOTAL DINNER COUNTS ======

  @rx.var(cache=False)
  def dinner_count(self) -> int:
      return len(self.dinner_signups)

  @rx.var(cache=False)
  def dinner_count_vegan(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.diet, str(Diet.VEGAN)):
              count += 1
      return count

  @rx.var(cache=False)
  def dinner_count_vegetarian(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.diet, str(Diet.VEGETARIAN)):
              count += 1
      return count

  @rx.var(cache=False)
  def dinner_count_meat(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.diet, str(Diet.MEAT)):
              count += 1
      return count
  

# ====== GET VOLUNTEERS DINNER COUNTS ======

  @rx.var(cache=False)
  def dinner_count_volunteers(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.item, str("Dinner sign-up (volunteer)")):
              count += 1
      return count
  
  @rx.var(cache=False)
  def dinner_count_vegan_volunteers(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.diet, str(Diet.VEGAN)) and str_cmp(order.item, str("Dinner sign-up (volunteer)")):
              count += 1
      return count

  @rx.var(cache=False)
  def dinner_count_vegetarian_volunteers(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.diet, str(Diet.VEGETARIAN)) and str_cmp(order.item, str("Dinner sign-up (volunteer)")):
              count += 1
      return count

  @rx.var(cache=False)
  def dinner_count_meat_volunteers(self) -> int:
      count = 0
      for order in self.dinner_signups:
          if str_cmp(order.diet, str(Diet.MEAT)) and str_cmp(order.item, str("Dinner sign-up (volunteer)")):
              count += 1
      return count
  @rx.var(cache=False)
  def get_user_debt(self) -> float:
    return sum([order.total for order in self.current_user_orders])
  
  @rx.var(cache=False)
  def get_all_nick_names(self) -> List[str]:
    return [user.nick_name for user in self.users]
