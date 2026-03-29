from datetime import datetime
import asyncio
from typing import Any, Dict, List, Optional, Literal
from urllib.parse import quote

import reflex as rx
import stripe

from sqlalchemy import update, select
from obhonesty.aux import (
    short_uid,
    generate_receiver_from_names,
    check_internet_connection,
)
from obhonesty.constants import true_values, DATETIME_FORMAT
from obhonesty.user import User
from obhonesty.item import Item
from obhonesty.order import Order
from obhonesty.sheet import order_sheet, user_sheet, stripe_payments_sheet
from obhonesty.models import (
    User as User_Model,
    Order as Order_Model,
    Item as Item_Model,
    Admin as Admin_Model,
    Meal as Meal_Model,
)

from dotenv import load_dotenv

load_dotenv()
import os
from gspread import Cell

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class State(rx.State):
    """The app state."""

    admin_data: Dict[str, Any] = {}
    users: List[User] = []
    items: Dict[str, Item] = {}
    todays_breakfast_meals: List[Meal_Model] = []
    todays_dinner_meals: List[Meal_Model] = []
    current_user: Optional[User] = None
    new_nick_name: str = ""
    custom_item_price: str = ""
    orders: List[Order] = []
    cancel_redirect: bool = False
    is_item_button_dialog_active: bool = False
    ordered_item: str = ""
    is_closing_account: Optional[bool] = None
    is_email_login_incorrect = False
    late_dinner_user_nick_name: Optional[str] = None
    show_stripe_connection_failure_message = False
    has_stripe_qr_generation_failed = False
    should_late_dinner_signup_form_reload = False
    item_uuid: str = ""

    # --- Meal Counts ---

    breakfast_count: int = 0
    breakfast_count_served: int = 0

    dinner_count: int = 0
    dinner_count_served: int = 0

    dinner_count_vegan: int = 0
    dinner_count_vegetarian: int = 0
    dinner_count_meat: int = 0

    dinner_count_guests: int = 0
    dinner_count_guests_served: int = 0
    dinner_count_guests_vegan: int = 0
    dinner_count_guests_vegetarian: int = 0
    dinner_count_guests_meat: int = 0

    dinner_count_volunteers: int = 0
    dinner_count_volunteers_served: int = 0
    dinner_count_volunteers_vegan: int = 0
    dinner_count_volunteers_vegetarian: int = 0
    dinner_count_volunteers_meat: int = 0

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
        self.dinner_signup_first_name = (
            self.current_user.first_name if self.current_user else ""
        )
        self.dinner_signup_last_name = (
            self.current_user.last_name if self.current_user else ""
        )
        self.dinner_signup_dietary_preference = (
            self.current_user.diet if self.current_user else ""
        )
        self.dinner_signup_allergies = (
            self.current_user.allergies if self.current_user else ""
        )

    @rx.event
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
        self.is_closing_account = None
        self.show_stripe_connection_failure_message = False
        self.has_stripe_qr_generation_failed = False

    @rx.event(background=True)
    async def set_served(
        self, meal_id: str, value: bool, meal_type: Literal["breakfast", "dinner"]
    ):
        meal_state = (
            self.todays_breakfast_meals
            if meal_type == "breakfast"
            else self.todays_dinner_meals
        )

        for index, meal in enumerate(meal_state):
            if meal.meal_id != meal_id:
                continue

            async with self:
                meal_state[index].served = value
            break

        with rx.session() as session:
            session.exec(
                update(Meal_Model)
                .where(Meal_Model.meal_id == meal_id)
                .values(served=value)
            )
            session.commit()

    def set_dinner_as_ordered_item(self):
        self.ordered_item = "dinner"

    @rx.event
    def set_late_dinner_user_nick_name(self, nick_name: str):
        self.late_dinner_user_nick_name = nick_name

    @rx.event
    def reset_late_dinner_user_nick_name(self):
        self.late_dinner_user_nick_name = None

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
            users = [
                User.from_dict(row.model_dump())
                for row in session.exec(User_Model.select_users_with_an_active_tab())
                .scalars()
                .all()
            ]
            todays_breakfast_meals = (
                session.execute(Meal_Model.select_todays_breakfast_meals())
                .scalars()
                .all()
            )
            todays_dinner_meals = (
                session.execute(Meal_Model.select_todays_dinner_meals()).scalars().all()
            )
            items = {}

            for row in session.exec(Item_Model.select()).all():
                if row.name == "":
                    continue

                items[row.name] = Item.from_dict(row.model_dump())

            orders = [
                Order.from_dict(row.model_dump())
                for row in session.exec(Order_Model.select()).all()
            ]
            admin_data = {}

            for row in session.exec(Admin_Model.select()).all():
                admin_data[row.key] = (
                    row.value if "deadline" in row.key else float(row.value)
                )

        async with self:
            self.items = items
            self.orders = orders
            self.users = users
            self.admin_data = admin_data
            self.todays_dinner_meals = todays_dinner_meals
            self.todays_breakfast_meals = todays_breakfast_meals

            if self.router.page.path in ["/admin/breakfast", "/admin/dinner"]:
                return State.update_meal_totals

    @rx.event
    def update_meal_totals(self):
        meal_totals = Meal_Model.get_todays_meal_counts()
        self.breakfast_count = meal_totals["breakfast"]["total"]
        self.breakfast_count_served = meal_totals["breakfast"]["served"]

        self.dinner_count_guests_served = meal_totals["dinner"]["guest"]["served"]
        self.dinner_count_guests_vegan = meal_totals["dinner"]["guest"]["vegan"]
        self.dinner_count_guests_vegetarian = meal_totals["dinner"]["guest"][
            "vegetarian"
        ]
        self.dinner_count_guests_meat = meal_totals["dinner"]["guest"]["meat"]
        self.dinner_count_guests = (
            self.dinner_count_guests_vegan
            + self.dinner_count_guests_vegetarian
            + self.dinner_count_guests_meat
        )

        self.dinner_count_volunteers_served = meal_totals["dinner"]["volunteer"][
            "served"
        ]
        self.dinner_count_volunteers_vegan = meal_totals["dinner"]["volunteer"]["vegan"]
        self.dinner_count_volunteers_vegetarian = meal_totals["dinner"]["volunteer"][
            "vegetarian"
        ]
        self.dinner_count_volunteers_meat = meal_totals["dinner"]["volunteer"]["meat"]
        self.dinner_count_volunteers = (
            self.dinner_count_volunteers_vegan
            + self.dinner_count_volunteers_vegetarian
            + self.dinner_count_volunteers_meat
        )

        self.dinner_count = self.dinner_count_volunteers + self.dinner_count_guests
        self.dinner_count_served = (
            self.dinner_count_volunteers_served + self.dinner_count_guests_served
        )

        self.dinner_count_volunteers_vegan + self.dinner_count_guests_vegan
        self.dinner_count_vegetarian = (
            self.dinner_count_volunteers_vegetarian
            + self.dinner_count_guests_vegetarian
        )
        self.dinner_count_meat = (
            self.dinner_count_volunteers_meat + self.dinner_count_guests_meat
        )

    @rx.event(background=True)
    async def reload_admin_dinner_data(self):
        while self.router.page.path in ["/admin/breakfast", "/admin/dinner"]:
            yield State.reload_sheet_data  # , State.update_meal_totals]
            await asyncio.sleep(10)

    @rx.event
    def handle_user_login_form_submit(self, form_data):
        user: Optional[User_Model] = None
        error_message: Optional[str] = None

        try:
            user = (
                rx.session()
                .exec(
                    select(User_Model).where(
                        User_Model.nick_name == form_data["user_nick_name"]
                    )
                )
                .scalar()
            )

        except:
            error_message = (
                "There has been an error with your account. Please see reception."
            )

        if not user:
            error_message = "Your account could not be found. Please see reception."

        if error_message:
            return rx.toast.error(error_message)

        if str(form_data["email_first_five_chars"]) != user.email[:5]:
            self.is_email_login_incorrect = True
            return

        self.current_user = User.from_dict(user.model_dump())
        self.is_email_login_incorrect = False
        return rx.redirect("/user")

    @rx.event
    def handle_user_login_dialog_open_change(self):
        self.is_email_login_incorrect = False

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
                    order_id=self.item_uuid
                    if self.is_stripe_session_paid
                    else str(short_uid()),
                    user_nick_name=self.current_user.nick_name,
                    time=now,
                    item=item.name,
                    quantity=quantity,
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
                    synced=False,
                )
            )
            session.commit()

        return rx.toast.info(
            f"'{item.name}' registered succesfully. Thank you!",
            position="bottom-center",
        )

    @rx.event
    def order_custom_item(self, form_data: dict):
        now = datetime.now().strftime(DATETIME_FORMAT)
        price = float(form_data["custom_item_price"])
        item_name = form_data["custom_item_name"]

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
                    tax_category=form_data["tax_category"],
                    comment=form_data["custom_item_description"],
                    paid=self.is_stripe_session_paid,
                    paid_time=now if self.is_stripe_session_paid else "",
                    method="stripe" if self.is_stripe_session_paid else "",
                    checkout_staff="tablet" if self.is_stripe_session_paid else "",
                    synced=False,
                )
            )
            session.commit()

        return rx.toast.info(
            f"'{item_name}' registered succesfully. Thank you!",
            position="bottom-center",
        )

    @rx.var(cache=False)
    def get_receiver(self) -> str:
        first_name = (
            self.dinner_signup_first_name
            if self.dinner_signup_first_name != ""
            else self.breakfast_signup_first_name
        )
        last_name = (
            self.dinner_signup_last_name
            if self.dinner_signup_last_name != ""
            else self.breakfast_signup_last_name
        )
        return generate_receiver_from_names(first_name, last_name)

    @rx.event
    def order_dinner(self):
        now = datetime.now().strftime(DATETIME_FORMAT)

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=self.item_uuid
                    if self.is_stripe_session_paid
                    else str(short_uid()),
                    user_nick_name=self.current_user.nick_name,
                    time=now,
                    item="Dinner sign-up",
                    quantity=1,
                    price=self.admin_data.get("dinner_price", 0),
                    total=self.admin_data.get("dinner_price", 0),
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
                    synced=False,
                )
            )
            session.commit()

        if not self.is_stripe_session_paid:
            # only redirect if the user hasn't paid with stripe
            self.current_order_request_id = ""
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
            return list(
                map(
                    lambda message: rx.toast.error(message),
                    missing_required_field_messages,
                )
            ) + [State.reset_order_request_id]

        # guests should not be able to sign up for multiple breakfasts, but they can sign up for multiple packed lunches
        if not self.breakfast_signup_item.lower().startswith(
            "packed lunch"
        ) and self.get_receiver in [order.receiver for order in self.breakfast_signups]:
            return [
                State.reset_order_request_id,
                rx.toast.error(
                    f"{self.get_receiver} is already signed up, "
                    "please provide different name if you want to sign up another person."
                ),
            ]

        if is_guest_paying_now:
            self.ordered_item = "breakfast"
            return State.generate_item_payment_qr

        return State.order_breakfast

    @rx.event
    def sign_guest_up_for_dinner(self, is_guest_paying_now: bool):
        if self.order_request_id != self.current_order_request_id:
            return

        if self.get_receiver in [order.receiver for order in self.dinner_signups]:
            return [
                State.reset_order_request_id,
                rx.toast.error(
                    f"{self.get_receiver} is already signed up, "
                    "please provide different name if you want to sign up another person."
                ),
            ]

        if is_guest_paying_now:
            self.ordered_item = "dinner"
            return State.generate_item_payment_qr

        return State.order_dinner

    @rx.event
    def handle_add_another_press_for_late_dinner_signup(self):
        self.should_late_dinner_signup_form_reload = True

    @rx.event
    def order_dinner_late(self, form_data: dict):
        now = datetime.now().strftime(DATETIME_FORMAT)
        price = self.admin_data.get("dinner_price", 0)

        with rx.session() as session:
            session.add(
                Order_Model(
                    order_id=str(short_uid()),
                    user_nick_name=form_data["nick_name"],
                    time=now,
                    item="Dinner sign-up",
                    quantity=1,
                    price=price,
                    total=price,
                    receiver=form_data["full_name"].upper().strip(),
                    diet=form_data["diet"],
                    allergies=form_data["allergies"],
                    served="",
                    tax_category="Food and beverage non-alcoholic",
                    comment="Late dinner signup",
                    paid=False,
                    paid_time="",
                    method="",
                    checkout_staff="",
                    synced=False,
                )
            )
            session.commit()

        yield rx.redirect(
            "/admin/dinner"
        ) if not self.should_late_dinner_signup_form_reload else rx.redirect(
            "/admin/late"
        )
        self.should_late_dinner_signup_form_reload = False

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
                    order_id=self.item_uuid
                    if self.is_stripe_session_paid
                    else str(short_uid()),
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
                    synced=False,
                )
            )
            session.commit()

        if not self.is_stripe_session_paid:
            # only redirect if the user hasn't paid with stripe
            return rx.redirect("/user")

    @rx.event
    def submit_signup(self, form_data: dict):
        with rx.session() as session:
            session.add(
                User_Model.model_validate(
                    {
                        **{key: str(form_data[key]) for key in form_data},
                        "synced": False,
                        "volunteer": False,
                        "away": False,
                    }
                )
            )
            session.commit()
        return rx.redirect("/")

    @rx.event
    def handle_checkout_choice(self, form_data: dict):
        self.is_closing_account = form_data["is_closing_account"] == "Yes"

    @rx.event
    def close_guest_account(self):
        with rx.session() as session:
            user_sheet_row_number: int
            all_users = session.exec(User_Model.select()).all()
            user_model: User_Model

            for index, user in enumerate(all_users):
                if user.nick_name != self.current_user.nick_name:
                    continue

                user_model = user
                user_sheet_row_number = index + 2
                break

            values = []

            if self.current_user.prepaid_dinners_quantity:
                # reduce prepaid dinners quantity (col 13) by the number of dinners paid for.
                # if no more dinners remain, clear the value
                prepaid_dinners_value = (
                    self.remaining_prepaid_dinners_count
                    if self.remaining_prepaid_dinners_count
                    else ""
                )
                values.append([13, prepaid_dinners_value])

            if self.is_closing_account:
                # if closing their account make this no longer an active tab (col 12)
                values.append([12, False])
                # updating the SQL row directly immediately removes the user from the user list on the welcome page.
                user_model.active_tab = False
                session.commit()

            if not len(values):
                return

            cells = []

            for col_num, value in values:
                cells.append(Cell(row=user_sheet_row_number, col=col_num, value=value))

            try:
                user_sheet.update_cells(cells, value_input_option="USER_ENTERED")

            except Exception as e:
                return rx.toast.error(f"Error updating cells: {e}")

    @rx.event
    def pay_current_tab(self):
        if not order_sheet:
            return rx.error("No backend connected")

        def filter_current_user_orders(order_enumerate: list[int, Order]) -> bool:
            order = order_enumerate[1]
            return (
                order.user_nick_name == self.current_user.nick_name
                and not order.paid_bool
            )

        current_users_unpaid_orders = list(
            filter(
                filter_current_user_orders,
                [[i + 2, v] for i, v in enumerate(self.orders)],
            )
        )
        cells = []
        now = datetime.now().strftime(DATETIME_FORMAT)

        for row_num, _ in current_users_unpaid_orders:
            for col_num, value in [
                [14, True],
                [15, now],
                [16, "stripe"],
                [17, "tablet"],
            ]:
                cells.append(Cell(row=row_num, col=col_num, value=value))
        try:
            order_sheet.update_cells(cells, value_input_option="USER_ENTERED")

        except Exception as e:
            return rx.toast.error(f"Error updating cells: {e}")

        return [rx.toast.success("Tab paid successfully!"), State.reload_sheet_data]

    # --- Payment Logic Handlers ---
    @rx.event(background=True)
    async def generate_item_payment_qr(
        self, item_name: str = "", unit_price: float = 0
    ):
        def generate_line_item(name: str, unit_amount: int, quantity: int):
            return {
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": name},
                    "unit_amount": unit_amount,
                },
                "quantity": quantity,
            }

        async with self:
            self.is_stripe_session_paid = False
            self.payment_qr_code = ""

        line_items = []

        if item_name == "tab":
            # sums up each item in the tab for a total quantity per item per price point to account for any price changes
            # eg. dinner x 3 @ €10 and dinner x 2 @ €12
            summarised_item_quantities = {}

            for order in self.current_user_orders:
                name = order.item
                unit_amount = int(order.price * 100)

                if order.order_id in self.prepaid_dinner_ids:
                    name += " (Prepaid)"
                    unit_amount = 0

                if name not in summarised_item_quantities:
                    summarised_item_quantities[name] = {}

                if unit_amount not in summarised_item_quantities[name]:
                    summarised_item_quantities[name][unit_amount] = 0

                summarised_item_quantities[name][unit_amount] += int(order.quantity)

            extra_line_item_total = 0
            last_item_total = 0

            for summarised_item in summarised_item_quantities:
                for summarised_item_price_point in summarised_item_quantities[
                    summarised_item
                ]:
                    summarised_item_quantity = summarised_item_quantities[
                        summarised_item
                    ][summarised_item_price_point]

                    # stripe cannot accept more than 100 line items in a checkout session.
                    # if there are more than 100 items then it should display a total with a note to see reception for a full receipt
                    if len(line_items) == 99:
                        last_item_total = (
                            summarised_item_price_point * summarised_item_quantity
                        )

                    if len(line_items) == 100:
                        extra_line_item_total += (
                            summarised_item_price_point * summarised_item_quantity
                        )
                        continue

                    line_items.append(
                        generate_line_item(
                            summarised_item,
                            summarised_item_price_point,
                            summarised_item_quantity,
                        )
                    )

            if extra_line_item_total:
                extra_line_item_total += last_item_total
                line_items[99] = generate_line_item(
                    "Remaining item total - see reception for full receipt",
                    extra_line_item_total,
                    1,
                )

        else:
            quantity = (
                self.temp_quantity
                if self.temp_quantity > 0
                and self.ordered_item not in ["breakfast", "dinner"]
                else 1.0
            )

            if self.ordered_item == "breakfast":
                item_name = self.breakfast_signup_item
                unit_price = self.get_breakfast_price

            if self.ordered_item == "dinner":
                item_name = "dinner"
                unit_price = self.admin_data["dinner_price"]

            line_items.append(
                generate_line_item(item_name, int(unit_price * 100), int(quantity))
            )

        # 1. Create Stripe Checkout Session

        ob_payment_id = str(short_uid())

        try:
            # This creates a payment page hosted by Stripe
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                metadata={"ob_payment_id": ob_payment_id},
                # payment_intent_data allows staff to track the payment through the stripe dashboard using the payment id
                payment_intent_data={"metadata": {"ob_payment_id": ob_payment_id}},
                success_url=os.getenv("SUCCESS_URL")
                if os.getenv("SUCCESS_URL")
                else "https://example.com/success",
                cancel_url=os.getenv("CANCEL_URL")
                if os.getenv("CANCEL_URL")
                else "https://example.com/cancel",
            )

            async with self:
                # 2. Generate QR Code pointing to that Stripe URL
                self.current_stripe_session_id = session.id
                self.payment_qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={quote(session.url)}"

        except Exception as e:
            print(f"Stripe Error: {e}", flush=True)

            async with self:
                self.has_stripe_qr_generation_failed = True

            return

        if self.current_stripe_session_id == "":
            return

        def generate_stripe_payment_row(order_id):
            return [
                str(short_uid()),
                datetime.now().strftime(DATETIME_FORMAT),
                self.current_stripe_session_id,
                ob_payment_id,
                order_id,
                self.current_user.nick_name,
            ]

        stripe_payment_rows_to_add = []

        if item_name == "tab":
            stripe_payment_rows_to_add = [
                generate_stripe_payment_row(order.order_id)
                for order in self.current_user_orders
            ]

        else:
            async with self:
                self.item_uuid = str(short_uid())

            stripe_payment_rows_to_add.append(
                generate_stripe_payment_row(self.item_uuid)
            )

        try:
            # log payment session so it can be tracked by staff in case of payment issues
            stripe_payments_sheet.append_rows(
                stripe_payment_rows_to_add,
                value_input_option="USER_ENTERED",
                table_range="A1",
            )
        except Exception as e:
            print(f"Error adding payments to stripe_payments_sheet: {e}")

        return State.check_stripe_payment_status

    @rx.event(background=True)
    async def check_stripe_payment_status(self):
        """Periodically checks if payment was successful"""
        stripe_error_message = ""

        while True:
            if self.current_stripe_session_id == "" or self.is_stripe_session_paid:
                return

            result = False

            try:
                check_internet_connection()
                session = stripe.checkout.Session.retrieve(
                    self.current_stripe_session_id
                )
                result = session.payment_status == "paid"
                stripe_error_message = ""

                async with self:
                    self.show_stripe_connection_failure_message = False

            except Exception as e:
                if stripe_error_message != str(e):
                    stripe_error_message = str(e)
                    print(
                        f"Stripe Error: {stripe_error_message} - {datetime.now()}",
                        flush=True,
                    )

                async with self:
                    self.show_stripe_connection_failure_message = True

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
            return [State.pay_current_tab, State.close_guest_account]

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
        self.is_closing_account = None
        self.show_stripe_connection_failure_message = False
        self.has_stripe_qr_generation_failed = False
        self.current_order_request_id = ""
        yield State.reset_order_request_id
        if (
            temp_ordered_item == "dinner" or temp_ordered_item == "breakfast"
        ) and temp_is_stripe_session_paid:
            return rx.redirect("/user")

    # -----------------------------------

    @rx.var(cache=False)
    def current_user_orders_in_reverse_chronological_order(self) -> List[Order]:
        current_user_orders_copy = self.current_user_orders.copy()
        current_user_orders_copy.reverse()
        return current_user_orders_copy

    @rx.var(cache=False)
    def current_user_orders(self) -> List[Order]:
        filtered: List[Order] = []
        if not self.current_user:
            return []

        for order in self.orders:
            if (
                order.user_nick_name == self.current_user.nick_name
                and not order.paid_bool
            ):
                order_copy: Order = order.copy()
                try:
                    order_copy.time = datetime.fromisoformat(order.time).strftime(
                        "%d/%m/%Y, %H:%M:%S"
                    )
                except BaseException:
                    pass

                filtered.append(order_copy)

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
            if len(str(float_val).split(".")[-1]) <= 2:
                return False
            return True
        except ValueError:
            return True

    @rx.var(cache=False)
    def dinner_signup_available(self) -> int:
        try:
            deadline = datetime.strptime(
                self.admin_data.get("dinner_signup_deadline", "22:59"), "%H:%M"
            )
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
                self.admin_data.get("breakfast_signup_deadline", "22:59"), "%H:%M"
            )
        except BaseException:
            deadline = datetime.strptime("22:59", "%H:%M")
        now = datetime.now()
        deadline_minutes = deadline.hour * 60 + deadline.minute
        now_minutes = now.hour * 60 + now.minute
        return now_minutes < deadline_minutes

    @rx.var(cache=False)
    def breakfast_signups(self) -> List[Order]:
        signups: List[Order] = []
        for order in self.orders:
            try:
                order_date = datetime.strptime(order.time, DATETIME_FORMAT).date()
            except BaseException:
                continue

            if (
                order.item == "Breakfast sign-up"
                and not order.item.lower().startswith("packed lunch")
                and order_date == datetime.today().date()
            ):
                order_alt = order.copy()
                try:
                    order_alt.time = datetime.fromisoformat(order.time).strftime(
                        "%H:%M:%S"
                    )
                except:
                    pass
                signups.append(order_alt)
        signups.sort(key=lambda x: x.time, reverse=True)
        return signups

    @rx.var(cache=False)
    def tonights_dinner_signups(self) -> List[Meal_Model]:
        return self.todays_dinner_meals

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
                        synced=True,
                    )
                )
        signups.sort(key=lambda x: x.receiver)
        signups.sort(key=lambda x: x.diet)
        signups.sort(key=lambda x: x.comment)
        return signups

    @rx.var(cache=False)
    def get_user_debt(self) -> float:
        return sum(
            [
                order.total
                for order in self.current_user_orders
                if order.order_id not in self.prepaid_dinner_ids
            ]
        )

    @rx.var(cache=False)
    def get_all_nick_names(self) -> List[str]:
        return [user.nick_name for user in self.users]

    @rx.var
    def remaining_prepaid_dinners_count(self) -> int:
        if not self.current_user:
            return 0

        prepaid_dinner_count: int = self.current_user.prepaid_dinners_quantity

        for order in self.current_user_orders:
            if not prepaid_dinner_count:
                return prepaid_dinner_count

            if order.item != "Dinner sign-up":
                continue

            prepaid_dinner_count -= 1

        return prepaid_dinner_count

    @rx.var
    def prepaid_dinner_ids(self) -> List[str]:
        if not self.current_user:
            return []

        return [
            o.order_id for o in self.current_user_orders if o.item == "Dinner sign-up"
        ][: self.current_user.prepaid_dinners_quantity]
