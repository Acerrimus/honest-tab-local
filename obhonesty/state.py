from datetime import datetime
import asyncio
from typing import Any, Dict, List, Optional
from urllib.parse import quote


import reflex as rx
import stripe

from sqlalchemy import update
from obhonesty.aux import short_uid, str_cmp, generate_receiver_from_names
from obhonesty.constants import Diet, true_values, DATETIME_FORMAT
from obhonesty.user import User
from obhonesty.item import Item
from obhonesty.order import Order
from obhonesty.sheet import user_sheet, item_sheet, order_sheet, admin_sheet
from obhonesty.models import User as User_Model, Order as Order_Model, Item as Item_Model, Admin as Admin_Model, Meal as Meal_Model

from dotenv import load_dotenv
load_dotenv()
import os
from gspread import Cell

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class State(rx.State):
    """The app state."""
    admin_data: Dict[str, Any] = {}
    users: List[User] = []
    items: Dict[str, Item] = {}
    tonights_dinner_meals: List[Meal_Model] = []
    current_user: Optional[User] = None
    new_nick_name: str = ""
    custom_item_price: str = ""
    orders: List[Order] = []
    cancel_redirect: bool = False
    is_item_button_dialog_active: bool = False
    ordered_item: str = ""

    
    # --- Payment State Variables ---
    current_stripe_session_id: str = ""
    payment_qr_code: str = ""
    is_stripe_session_paid: bool = False
    is_stripe_dialog_active: bool = False
    # ------------------------------------

    # --- Item Payment State ---
    temp_quantity: float = 1.0 

    # --- Signup button state
    order_request_id: str = ""
    current_order_request_id: str = ""

    # --- Breakfast state ---
    breakfast_signup_first_name: str = ""
    breakfast_signup_last_name: str = ""
    breakfast_signup_item: str = ""
    breakfast_signup_allergies: str = ""

    # --- Dinner State ---
    dinner_signup_first_name: str = ""
    dinner_signup_last_name: str = ""
    dinner_signup_dietary_preference: str = ""
    dinner_signup_allergies: str = ""
    # -----------------------------

    def set_temp_quantity(self, value: str):
        try:
            self.temp_quantity = float(value)
        except ValueError:
            self.temp_quantity = 1.0

    @rx.var(cache=False)
    def is_order_request_loading(self) -> bool:
        return self.current_order_request_id != ""
        
    @rx.event
    def set_order_request_id(self):
        request_id = str(short_uid())
        self.order_request_id = request_id

        if self.current_order_request_id != "":
            return
        
        self.current_order_request_id = request_id

    @rx.event
    def reset_order_request_id(self):
        self.order_request_id = ""
        self.current_order_request_id = ""

    def set_breakfast_signup_default_values(self):
        self.breakfast_signup_first_name = self.current_user.first_name
        self.breakfast_signup_last_name = self.current_user.last_name
        self.breakfast_signup_item = ""
        self.breakfast_signup_allergies = self.current_user.allergies
        
    def set_breakfast_signup_first_name(self, value: str):
        self.breakfast_signup_first_name = value.strip()

    def set_breakfast_signup_last_name(self, value: str):
        self.breakfast_signup_last_name = value.strip()

    def set_breakfast_signup_item(self, value: str):
        self.breakfast_signup_item = value

    def set_breakfast_signup_allergies(self, value: str):
        self.breakfast_signup_allergies = value.strip()

    def set_dinner_signup_first_name(self, value: str):
        self.dinner_signup_first_name = value.strip()

    def set_dinner_signup_last_name(self, value: str):
        self.dinner_signup_last_name = value.strip()

    def set_dinner_dietary_preference(self, value: str):
        self.dinner_signup_dietary_preference = value

    def set_dinner_allergies(self, value: str):
        self.dinner_signup_allergies = value.strip()

    def set_dinner_signup_default_values(self):
        self.dinner_signup_first_name = self.current_user.first_name if self.current_user else ""
        self.dinner_signup_last_name = self.current_user.last_name if self.current_user else ""
        self.dinner_signup_dietary_preference = self.current_user.diet if self.current_user else ""
        self.dinner_signup_allergies = self.current_user.allergies if self.current_user else ""

    def clear_temp_state_values(self):
        self.is_item_button_dialog_active = False
        self.dinner_signup_first_name = ""
        self.dinner_signup_last_name = ""
        self.dinner_signup_dietary_preference = ""
        self.dinner_signup_allergies = ""
        self.breakfast_signup_first_name = ""
        self.breakfast_signup_last_name = ""
        self.breakfast_signup_item = ""
        self.dinner_signup_allergies = ""
        self.current_stripe_session_id = ""
        self.payment_qr_code = ""
        self.is_stripe_session_paid = False
        self.is_stripe_dialog_active = False
        self.ordered_item = ""
        self.order_request_id = ""
        self.current_order_request_id = ""

    @rx.event(background=True)
    async def set_served(self, meal_id: str, value: bool):
        for index, meal in enumerate(self.tonights_dinner_meals):
            if meal.meal_id != meal_id:
                continue
            
            async with self:
                self.tonights_dinner_meals[index].served = value
            break
        
        with rx.session() as session:
            session.exec(
                update(Meal_Model).where(Meal_Model.meal_id == meal_id).values(served=value)
            )
            session.commit()

    def set_dinner_as_ordered_item(self):
        self.ordered_item = "dinner"

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
        with rx.session() as session:
              users = [User.from_dict(row.model_dump()) for row in session.exec(User_Model.select()).all()]
              tonights_dinner_meals = session.execute(Meal_Model.select_todays_dinner_meals()).scalars().all()
              items = {}

              for row in session.exec(Item_Model.select()).all():
                  if row.name == "":
                    continue

                  items[row.name] = Item.from_dict(row.model_dump())

              orders = [Order.from_dict(row.model_dump()) for row in session.exec(Order_Model.select()).all()]
              admin_data = {}

              for row in session.exec(Admin_Model.select()).all():
                  admin_data[row.key] = row.value if "deadline" in row.key else float(row.value)

        async with self:
              self.items = items
              self.orders = orders
              self.users = users
              self.admin_data = admin_data
              self.tonights_dinner_meals = tonights_dinner_meals
        
    @rx.event(background=True)
    async def reload_admin_dinner_data(self):
        while self.router.page.path == "/admin/dinner":
            yield State.reload_sheet_data
            await asyncio.sleep(10)

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
    def order_item(self):
        item = self.items[self.ordered_item]

        try:
            quantity = float(self.temp_quantity)

        except BaseException:
            return rx.toast.error("Failed to register. Quantity must be a number")

        now = datetime.now().strftime(DATETIME_FORMAT)

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=str(short_uid()),
                    user_nick_name=self.current_user.nick_name,
                    time=now,
                    item=item.name,
                    quantity=1,
                    price=item.price,
                    total=quantity * item.price,
                    receiver="",
                    diet="",
                    allergies="",
                    served="",
                    tax_category=item.tax_category,
                    comment="",
                    paid=self.is_stripe_session_paid,
                    paid_time=now if self.is_stripe_session_paid else "",
                    method="stripe" if self.is_stripe_session_paid else "",
                    checkout_staff="tablet" if self.is_stripe_session_paid else "",
                    synced=False
                )
            )
            session.commit()

        return rx.toast.info(
            f"'{item.name}' registered succesfully. Thank you!",
            position="bottom-center"
        )

    @rx.event
    def order_custom_item(self, form_data: dict):
        now = datetime.now().strftime(DATETIME_FORMAT)
        price = float(form_data['custom_item_price'])
        item_name = form_data['custom_item_name']

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=str(short_uid()),
                    user_nick_name=self.current_user.nick_name,
                    time=now,
                    item=item_name,
                    quantity=1,
                    price=price,
                    total=price,
                    receiver="",
                    diet="",
                    allergies="",
                    served="",
                    tax_category=form_data['tax_category'],
                    comment=form_data['custom_item_description'],
                    paid=self.is_stripe_session_paid,
                    paid_time=now if self.is_stripe_session_paid else "",
                    method="stripe" if self.is_stripe_session_paid else "",
                    checkout_staff="tablet" if self.is_stripe_session_paid else "",
                    synced=False
                )
            )
            session.commit()

        return rx.toast.info(
            f"'{item_name}' registered succesfully. Thank you!",
            position="bottom-center"
        )


    @rx.var(cache=False)
    def get_receiver(self) -> str:
        first_name = self.dinner_signup_first_name if self.dinner_signup_first_name != "" else self.breakfast_signup_first_name
        last_name = self.dinner_signup_last_name if self.dinner_signup_last_name != "" else self.breakfast_signup_last_name
        return generate_receiver_from_names(first_name, last_name)
        
    @rx.event
    def order_dinner(self):
        now = datetime.now().strftime(DATETIME_FORMAT)

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=str(short_uid()),
                    user_nick_name=self.current_user.nick_name,
                    time=now,
                    item="Dinner sign-up",
                    quantity=1,
                    price=self.admin_data.get('dinner_price', 0),
                    total=self.admin_data.get('dinner_price', 0),
                    receiver=self.get_receiver,
                    diet=self.dinner_signup_dietary_preference,
                    allergies=self.dinner_signup_allergies,
                    served="",
                    tax_category="Food and beverage non-alcoholic",
                    comment="",
                    paid=self.is_stripe_session_paid,
                    paid_time=now if self.is_stripe_session_paid else "",
                    method="stripe" if self.is_stripe_session_paid else "",
                    checkout_staff="tablet" if self.is_stripe_session_paid else "",
                    synced=False
                )
            )
            session.commit()
        
        if not self.is_stripe_session_paid:
            # only redirect if the user hasn't paid with stripe
            return rx.redirect("/user")


    @rx.event
    def sign_guest_up_for_breakfast(self, is_guest_paying_now: bool):
      if self.order_request_id != self.current_order_request_id:
          return
      
      # Check for missing required fields
      missing_required_field_messages: list[str] = []
      
      def append_missing_field_message(message_suffix):
          missing_required_field_messages.append(f"MISSING FIELD - {message_suffix}")

      if self.breakfast_signup_first_name == "":
          append_missing_field_message("Please enter a first name.")

      if self.breakfast_signup_last_name == "":
          append_missing_field_message("Please enter a last name.")
        
      if self.breakfast_signup_item == "":
          append_missing_field_message("Please select a breakfast item to order")

      if len(missing_required_field_messages):
          return list(map(lambda message: rx.toast.error(message), missing_required_field_messages)) + [State.reset_order_request_id]

      # guests should not be able to sign up for multiple breakfasts, but they can sign up for multiple packed lunches
      if not self.breakfast_signup_item.lower().startswith("packed lunch") and self.get_receiver in [
            order.receiver for order in self.breakfast_signups
        ]:
            return [State.reset_order_request_id, rx.toast.error(
                f"{self.get_receiver} is already signed up, "
                "please provide different name if you want to sign up another person.")]
      
      if is_guest_paying_now:
          self.ordered_item = "breakfast"
          return State.generate_item_payment_qr
      
      return State.order_breakfast

    @rx.event
    def sign_guest_up_for_dinner(self, is_guest_paying_now: bool):
        if self.order_request_id != self.current_order_request_id:
            return
        
        if self.get_receiver in [order.receiver for order in self.dinner_signups]:
            return [State.reset_order_request_id, rx.toast.error(
                f"{self.get_receiver} is already signed up, "
                "please provide different name if you want to sign up another person.")]
        
        if is_guest_paying_now:
            self.ordered_item = "dinner"
            return State.generate_item_payment_qr
        
        return State.order_dinner
    
    
    @rx.event
    def order_dinner_late(self, form_data: dict):
        now = datetime.now().strftime(DATETIME_FORMAT)
        price = self.admin_data.get('dinner_price', 0)

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=str(short_uid()),
                    user_nick_name=form_data['nick_name'],
                    time=now,
                    item="Dinner sign-up",
                    quantity=1,
                    price=price,
                    total=price,
                    receiver=form_data['full_name'].upper().strip(),
                    diet=form_data['diet'],
                    allergies=form_data['allergies'],
                    served="",
                    tax_category="Food and beverage non-alcoholic",
                    comment="Late dinner signup",
                    paid=False,
                    paid_time="",
                    method="",
                    checkout_staff="",
                    synced=False
                )
            )
            session.commit()
            
        return rx.redirect("/admin/dinner")

    @rx.var(cache=False)
    def get_breakfast_price(self) -> float:
        return self.admin_data.get(f"{self.breakfast_signup_item}_price", 0.0)

    @rx.event
    def order_breakfast(self):
        price = self.get_breakfast_price if not self.current_user.volunteer else 0.0
        now = datetime.now().strftime(DATETIME_FORMAT)

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=str(short_uid()),
                    user_nick_name=self.current_user.nick_name,
                    time=now,
                    item="Breakfast sign-up",
                    quantity=1,
                    price=price,
                    total=price,
                    receiver=self.get_receiver,
                    diet=self.breakfast_signup_item,
                    allergies=self.breakfast_signup_allergies,
                    served="",
                    tax_category="Food and beverage non-alcoholic",
                    comment="",
                    paid=self.is_stripe_session_paid,
                    paid_time=now if self.is_stripe_session_paid else "",
                    method="stripe" if self.is_stripe_session_paid else "",
                    checkout_staff="tablet" if self.is_stripe_session_paid else "",
                    synced=False
                )
            )
            session.commit()

        if not self.is_stripe_session_paid:
            # only redirect if the user hasn't paid with stripe
            return rx.redirect("/user")

    @rx.event
    def submit_signup(self, form_data: dict):
        print(form_data, flush=True)
        
        with rx.session() as session:
            session.add(User_Model.model_validate({
                **{key: str(form_data[key]) for key in form_data},
                "synced": False, "volunteer": False, "away": False}))
            session.commit()
        return rx.redirect("/")
    
    @rx.event
    def pay_current_tab(self):
        if not order_sheet:
            return rx.error("No backend connected")
        
        def filter_current_user_orders(order_enumerate: list[int, Order]) -> bool:
            order = order_enumerate[1]
            return order.user_nick_name == self.current_user.nick_name and not order.paid_bool
        
        current_users_unpaid_orders = list(filter(filter_current_user_orders, [[i + 2, v] for i, v in enumerate(self.orders)]))
        cells = []
        now = datetime.now().strftime(DATETIME_FORMAT)

        for row_num, _ in current_users_unpaid_orders:
            for col_num, value in [
                  [14, True],
                  [15, now],
                  [16, "stripe"],
                  [17, "tablet"]
                ]:
                  cells.append(Cell(row=row_num, col=col_num, value=value))
        try:
            order_sheet.update_cells(cells, value_input_option="USER_ENTERED")

        except Exception as e:
            return rx.toast.error(f"Error updating cells: {e}")
        
        return [
            rx.toast.success("Tab paid successfully!"),
            State.reload_sheet_data
        ]

    # --- Payment Logic Handlers ---
    @rx.event(background=True)
    async def generate_item_payment_qr(self, item_name: str= "", unit_price: float=0):
        """Generates a Stripe QR for a specific item * quantity"""
        async with self:
            self.is_stripe_session_paid = False
            self.payment_qr_code = "" 
        
        if self.ordered_item == "breakfast":
            item_name = self.breakfast_signup_item
            unit_price = self.get_breakfast_price

        if self.ordered_item == "dinner":
            item_name = "dinner"
            unit_price = self.admin_data['dinner_price']

        # Calculate total for this specific transaction
        quantity = self.temp_quantity if self.temp_quantity > 0 else 1.0
        total_amount = unit_price * quantity
        
        # Stripe expects amounts in cents (integers)
        amount_in_cents = int(total_amount * 100)

        # 1. Create Stripe Checkout Session
        try:
            # This creates a payment page hosted by Stripe
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': "Honesty bar tab" if item_name == "tab" else f"{quantity}x {item_name} (Self-Service)",
                        },
                        'unit_amount': amount_in_cents, # Total amount for the line
                    },
                    'quantity': 1, # We calculated total already, so line quantity is 1
                }],
                mode='payment',
                success_url='https://example.com/success', # Replace with your app URL
                cancel_url='https://example.com/cancel',
            )

            async with self:
                # 2. Generate QR Code pointing to that Stripe URL
                self.current_stripe_session_id = session.id
                self.payment_qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(session.url)}"

        except Exception as e:
            print(f"Stripe Error: {e}")
            async with self:
                # Fallback for testing if no API key is set
                qr_data = f"Stripe Config Missing. Pay €{total_amount:.2f} for {item_name}"
                self.payment_qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={qr_data}"

        if self.current_stripe_session_id != "":
            return State.check_stripe_payment_status

    @rx.event(background=True)
    async def check_stripe_payment_status(self):
        """Periodically checks if payment was successful"""
        while True:
            if self.current_stripe_session_id == "" or self.is_stripe_session_paid:
                return
            
            result = False
            
            try:
                session = stripe.checkout.Session.retrieve(self.current_stripe_session_id)
                result = session.payment_status == "paid"
                
            except Exception as e:
                print(f"Stripe Error: {e}")

            if not result:
                await asyncio.sleep(1)
                continue
              
            async with self:
                self.is_stripe_session_paid = True

            if self.ordered_item != "":
                if self.ordered_item == "dinner":
                    return State.order_dinner

                if self.ordered_item == "breakfast":
                    return State.order_breakfast
                
                return State.order_item
            
            # if no item has been ordered then it must be the entire tab.
            return State.pay_current_tab

    def open_item_dialog(self, item_name: str):
        self.temp_quantity = 1
        self.ordered_item = item_name

    @rx.event
    def show_stripe_item_payment_dialog(self, item_name: str, amount: float):
        if self.current_order_request_id != self.order_request_id:
            return
        
        self.is_stripe_dialog_active = True
        return State.generate_item_payment_qr(item_name, amount)

    @rx.event
    def close_item_dialog(self):
        temp_ordered_item = self.ordered_item
        temp_is_stripe_session_paid = self.is_stripe_session_paid
        self.payment_qr_code = ""
        self.current_stripe_session_id = ""
        self.is_stripe_session_paid = False
        self.is_stripe_dialog_active = False
        self.ordered_item = ""
        yield State.reset_order_request_id
        if [temp_ordered_item == "dinner" or temp_ordered_item == "breakfast"] and temp_is_stripe_session_paid:
            return rx.redirect("/user")


    # -----------------------------------

    @rx.var(cache=False)
    def current_user_orders(self) -> List[Order]:
        filtered: List[Order] = []
        if not self.current_user:
            return []
            
        for order in self.orders:
            if order.user_nick_name == self.current_user.nick_name and not order.paid_bool:
                order_copy = order.copy()
                try:
                    order_copy.time = datetime.fromisoformat(
                        order.time).strftime("%d/%m/%Y, %H:%M:%S")
                except BaseException:
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
            float_val = float(self.custom_item_price)
            if len(str(float_val).split('.')[-1]) <= 2:
                return False
            return True
        except ValueError:
            return True

    @rx.var(cache=False)
    def dinner_signup_available(self) -> int:
        try:
            deadline = datetime.strptime(
                self.admin_data.get('dinner_signup_deadline', "22:59"), "%H:%M")
        except BaseException:
            deadline = datetime.strptime("22:59", "%H:%M")
        now = datetime.now()
        deadline_minutes = deadline.hour * 60 + deadline.minute
        now_minutes = now.hour * 60 + now.minute
        return now_minutes < deadline_minutes

    @rx.var(cache=False)
    def breakfast_signup_available(self) -> bool:
        try:
            deadline = datetime.strptime(
                self.admin_data.get('breakfast_signup_deadline', "22:59"), "%H:%M")
        except BaseException:
            deadline = datetime.strptime("22:59", "%H:%M")
        now = datetime.now()
        deadline_minutes = deadline.hour * 60 + deadline.minute
        now_minutes = now.hour * 60 + now.minute
        return now_minutes < deadline_minutes

    @rx.var(cache=False)
    def tax_categories(self) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for order in self.orders:
            if order.tax_category not in result:
                result[order.tax_category] = 0.0
            result[order.tax_category] += order.price
        return result

    @rx.var(cache=False)
    def breakfast_signups(self) -> List[Order]:
        signups: List[Order] = []
        for order in self.orders:
            try:
                order_date = datetime.strptime(order.time, DATETIME_FORMAT).date()
            except BaseException:
                continue
            
            if order.item == "Breakfast sign-up" and not order.item.lower().startswith("packed lunch") and order_date == datetime.today().date():
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
    def tonights_dinner_signups(self) -> List[Meal_Model]:
        return self.tonights_dinner_meals

    @rx.var(cache=False)
    def dinner_signups(self) -> List[Order]:
        signups: List[Order] = []
        for order in self.orders:
            try:
                order_date = datetime.strptime(order.time, DATETIME_FORMAT).date()
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
                        comment=true_values[0],
                        # Not synced but necessary to avoid reflex from crashing at runtime.
                        # These order objects never interact with the db or google sheet so this is an arbitrary value.
                        synced=True))
        signups.sort(key=lambda x: x.receiver)
        signups.sort(key=lambda x: x.diet)
        signups.sort(key=lambda x: x.comment)
        return signups


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