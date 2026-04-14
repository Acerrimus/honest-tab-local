"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from sqlalchemy import select
import asyncio
from datetime import datetime

from obhonesty.pages import *
from obhonesty.state import State
from obhonesty.sheet import (
    user_sheet,
    item_sheet,
    order_sheet,
    admin_sheet,
    stripe_payments_sheet,
    payments_sheet,
)
from obhonesty.models import (
    User as User_Model,
    Order as Order_Model,
    Item as Item_Model,
    Admin as Admin_Model,
    Meal as Meal_Model,
    Stripe_Checkout_Session,
    Payment,
)
from obhonesty.aux import (
    check_internet_connection,
    get_model_string_type_columns,
    sanitise_record_strings,
    short_uid,
    generate_receiver_from_names,
)
from obhonesty.constants import DATETIME_FORMAT
from obhonesty.api.test_setup import fastapi_app

import os

is_test_environment = True if os.getenv("TEST") else False

app = rx.App() if not is_test_environment else rx.App(api_transformer=fastapi_app)

app.add_page(
    index,
    route="/",
    on_load=[
        State.reset_stripe_dialog_active_state,
        State.clear_temp_state_values,
        State.reload_sheet_data,
    ],
)
app.add_page(
    user_page,
    route="/user",
    on_load=[
        State.clear_temp_state_values,
        State.on_user_login,
        State.reload_sheet_data,
    ],
)
app.add_page(user_signup_page, route="/signup", on_load=State.cancel_timeout)
app.add_page(dinner_signup_page, route="/dinner", on_load=State.cancel_timeout)
app.add_page(breakfast_signup_page, route="/breakfast", on_load=State.cancel_timeout)
app.add_page(custom_item_page, route="/custom_item", on_load=State.cancel_timeout)
app.add_page(
    user_info_page,
    route="/info",
    on_load=[State.reload_sheet_data, State.cancel_timeout],
)
app.add_page(
    admin,
    route="/admin",
    on_load=[State.clear_temp_state_values, State.reload_sheet_data],
)
app.add_page(
    admin_dinner, route="/admin/dinner", on_load=State.reload_admin_dinner_data
)
app.add_page(
    admin_breakfast, route="/admin/breakfast", on_load=State.reload_admin_dinner_data
)
app.add_page(admin_user_page, route="/admin/user", on_load=State.reload_sheet_data)
app.add_page(
    late_dinner_signup_page,
    route="/admin/late",
    on_load=[State.reset_late_dinner_user_nick_name, State.reload_sheet_data],
)


def get_records(sheet, headers: list[str] = [], add_synced: bool = False):
    check_internet_connection()

    if sheet is None:
        return []

    records = sheet.get_all_records(expected_headers=headers)

    for record in records:
        if "" in record:
            del record[""]

    if not add_synced:
        return records

    return [{**record, "synced": True} for record in records]


def sync_new_orders(unsynced_orders):
    new_rows = []
    for order in unsynced_orders:
        new_rows.append(
            [
                order.order_id,
                order.user_nick_name,
                order.time,
                order.item,
                order.quantity,
                order.price,
                order.total,
                order.receiver,
                order.diet,
                order.allergies,
                order.served,
                order.tax_category,
                order.comment,
            ]
        )
    order_sheet.append_rows(
        new_rows, value_input_option="USER_ENTERED", table_range="A1"
    )


def sync_new_users(unsynced_users):
    new_rows = []
    for user in unsynced_users:

        new_rows.append(
            [
                user.nick_name,
                user.first_name,
                user.last_name,
                user.phone_number,
                user.email,
                user.diet,
                user.allergies,
                user.volunteer,
                user.away,
                "",
                user.current_guest,
                user.active_tab,
                "",
            ]
        )
    user_sheet.append_rows(
        new_rows, value_input_option="USER_ENTERED", table_range="A1"
    )


def sync_orders():
    order_string_columns = get_model_string_type_columns(Order_Model)

    with rx.session() as session:
        order_data = get_records(
            order_sheet,
            [
                "order_id",
                "user",
                "time",
                "item",
                "quantity",
                "price",
                "total",
                "diet",
                "allergies",
                "served",
                "tax_category",
                "comment",
            ],
            True,
        )
        current_unsynced_orders = (
            session.query(Order_Model).filter(~Order_Model.synced).all()
        )

        if not len(current_unsynced_orders):
            for order in order_data:
                order["user_nick_name"] = order["user"]
                del order["user"]
                sanitise_record_strings(order_string_columns, order)

            for row in session.exec(Order_Model.select()).all():
                session.delete(row)

            session.add_all(Order_Model.model_validate(order) for order in order_data)

        google_sheet_order_ids = [order["order_id"] for order in order_data]
        remaining_unsynced_orders = []

        for order in current_unsynced_orders:
            if order.order_id in google_sheet_order_ids:
                order.synced = True
                continue

            remaining_unsynced_orders.append(order)

        if len(session.new) or len(session.dirty):
            session.commit()

        if len(remaining_unsynced_orders):
            sync_new_orders(remaining_unsynced_orders)


def sync_users():
    user_string_columns = get_model_string_type_columns(User_Model)

    with rx.session() as session:
        user_data = get_records(
            user_sheet,
            [
                "nick_name",
                "first_name",
                "last_name",
                "phone_number",
                "email",
                "diet",
                "allergies",
                "volunteer",
                "away",
                "owes",
                "current_guest",
                "active_tab",
                "prepaid_dinners_quantity",
            ],
            True,
        )
        current_unsynced_users = (
            session.query(User_Model).filter(~User_Model.synced).all()
        )

        for user in user_data:
            del user["owes"]
            for key in ["volunteer", "away", "current_guest", "active_tab"]:
                user[key] = user[key].lower() in ["yes", "true"]

            user = sanitise_record_strings(user_string_columns, user)
            user["prepaid_dinners_quantity"] = (
                0
                if user["prepaid_dinners_quantity"] == ""
                else int(user["prepaid_dinners_quantity"])
            )

        if not len(current_unsynced_users):
            for row in session.exec(User_Model.select()).all():
                session.delete(row)

            session.add_all(User_Model.model_validate(user) for user in user_data)

        google_sheet_user_nick_names = [user["nick_name"] for user in user_data]
        remaining_unsynced_users = []

        for user in current_unsynced_users:
            if user.nick_name in google_sheet_user_nick_names:
                user.synced = True
                continue

            remaining_unsynced_users.append(user)

        if len(session.new) or len(session.dirty):
            session.commit()

        if len(remaining_unsynced_users):
            sync_new_users(remaining_unsynced_users)


def sync_items():
    with rx.session() as session:
        item_data = get_records(
            item_sheet, ["name", "price", "description", "tax_category"]
        )

        for row in session.exec(Item_Model.select()).all():
            session.delete(row)

        session.add_all(Item_Model.model_validate(item) for item in item_data)

        # seeds a test item for e2e testing if it doesn't already exist
        if is_test_environment:
            test_item_exists = False
            for item in item_data:
                if item["name"] != "TEST ITEM":
                    continue
                test_item_exists = True
                break

            if not test_item_exists:
                session.add(
                    Item_Model.model_validate(
                        {
                            "name": "TEST ITEM",
                            "price": 1.0,
                            "description": "",
                            "tax_category": "Miscellaneous",
                            "icon": "",
                        }
                    )
                )

        session.commit()


def sync_admin_data():
    with rx.session() as session:
        admin_data = get_records(admin_sheet)[0]

        for row in session.exec(Admin_Model.select()).all():
            session.delete(row)

        session.add_all(
            Admin_Model.model_validate({"key": key, "value": str(admin_data[key])})
            for key in admin_data
        )

        session.commit()


def update_meals_table():
    with rx.session() as session:
        volunteers: list[User_Model] = (
            session.exec(select(User_Model).where(User_Model.volunteer == True))
            .scalars()
            .all()
        )
        orders: list[Order_Model] = session.exec(Order_Model.select()).all()
        now = datetime.now()
        todays_meals: list[Meal_Model] = (
            session.execute(Meal_Model.select_todays_meals()).scalars().all()
        )
        dinner_meals_today: list[Meal_Model] = (
            session.execute(Meal_Model.select_todays_dinner_meals()).scalars().all()
        )
        signups_in_todays_orders = list(
            filter(
                lambda order: (
                    order.item == "Breakfast sign-up" or order.item == "Dinner sign-up"
                )
                and datetime.strptime(order.time, DATETIME_FORMAT).date() == now.date(),
                orders,
            )
        )
        signups_in_todays_orders_as_order_ids = list(
            map(lambda order: order.order_id, signups_in_todays_orders)
        )

        # remove guest meals from today's signups if they've been removed from orders
        for meal in todays_meals:
            # if order_id is "N/A" they are a volunteer getting dinner automatically, so this meal will not appear in the order table
            if (
                meal.order_id in signups_in_todays_orders_as_order_ids
                or meal.order_id == "N/A"
            ):
                continue

            session.delete(meal)

        dinner_meals_today_as_receivers = list(
            map(lambda meal: meal.receiver, dinner_meals_today)
        )

        # add volunteers to today's dinner meals if not already added
        for volunteer in volunteers:
            volunteer_receiver_name = generate_receiver_from_names(
                volunteer.first_name, volunteer.last_name
            )

            if volunteer_receiver_name in dinner_meals_today_as_receivers:
                continue

            session.add(
                Meal_Model(
                    meal_id=str(short_uid()),
                    order_id="N/A",
                    user_nick_name=volunteer.nick_name,
                    receiver=volunteer_receiver_name,
                    order_time=now,
                    meal_type="dinner",
                    diet=volunteer.diet,
                    allergies=volunteer.allergies,
                    volunteer=True,
                    served=False,
                )
            )

        todays_meals_as_order_ids = list(map(lambda meal: meal.order_id, todays_meals))

        # add new orders to today's meals if not already added
        for order in signups_in_todays_orders:
            if order.order_id in todays_meals_as_order_ids:
                continue

            session.add(
                Meal_Model(
                    meal_id=str(short_uid()),
                    order_id=order.order_id,
                    user_nick_name=order.user_nick_name,
                    receiver=order.receiver,
                    order_time=datetime.strptime(order.time, DATETIME_FORMAT),
                    meal_type="breakfast"
                    if order.item == "Breakfast sign-up"
                    else "dinner",
                    diet=order.diet,
                    allergies=order.allergies,
                    volunteer=False,
                    served=False,
                )
            )

        if len(session.new) or len(session.dirty) or len(session.deleted):
            session.commit()


def sync_new_stripe_checkout_sessions():
    stripe_checkout_session_records = get_records(
        stripe_payments_sheet,
        [
            "payment_order_id",
            "datetime_requested",
            "stripe_payment_id",
            "ob_payment_id",
            "order_id",
            "user",
        ],
    )
    stripe_checkout_session_record_payment_ids: list[str] = [
        checkout_session["payment_order_id"]
        for checkout_session in stripe_checkout_session_records
    ]
    remaining_unsynced_sessions: list[Stripe_Checkout_Session] = []

    with rx.session() as session:
        unsynced_stripe_checkout_session_rows = (
            session.query(Stripe_Checkout_Session)
            .filter(~Stripe_Checkout_Session.synced)
            .all()
        )

        for unsynced_session in unsynced_stripe_checkout_session_rows:
            if (
                unsynced_session.payment_order_id
                in stripe_checkout_session_record_payment_ids
            ):
                unsynced_session.synced = True
                continue

            remaining_unsynced_sessions.append(unsynced_session)

        if len(session.new) or len(session.dirty) or len(session.deleted):
            session.commit()

    if not len(remaining_unsynced_sessions):
        return

    stripe_payments_sheet.append_rows(
        [
            [
                remaining_unsynced_session.payment_order_id,
                remaining_unsynced_session.datetime_requested,
                remaining_unsynced_session.stripe_payment_id,
                remaining_unsynced_session.ob_payment_id,
                remaining_unsynced_session.order_id,
                remaining_unsynced_session.user,
            ]
            for remaining_unsynced_session in remaining_unsynced_sessions
        ],
        value_input_option="USER_ENTERED",
        table_range="A1",
    )


def sync_payments():
    payment_data = get_records(
        payments_sheet,
        [
            "order_id",
            "paid_time",
            "method",
            "checkout_staff",
        ],
    )
    payment_order_ids: list[str] = [payment["order_id"] for payment in payment_data]

    with rx.session() as session:
        unsynced_payments: list[Payment] = (
            session.query(Payment)
            .filter(Payment.order_id.not_in(payment_order_ids))
            .all()
        )

        if len(unsynced_payments):
            session.close()
            payments_sheet.append_rows(
                [
                    [
                        unsynced_payment.order_id,
                        unsynced_payment.paid_time,
                        unsynced_payment.method,
                        unsynced_payment.checkout_staff,
                    ]
                    for unsynced_payment in unsynced_payments
                ],
                value_input_option="USER_ENTERED",
                table_range="A1",
            )
            return

        for row in session.exec(Payment.select()).all():
            session.delete(row)

        session.add_all(Payment.model_validate(payment) for payment in payment_data)
        session.commit()


async def sync_google_sheet_and_local_db():
    sync_orders()
    await asyncio.sleep(1)
    sync_users()
    await asyncio.sleep(1)
    sync_items()
    await asyncio.sleep(1)
    sync_admin_data()
    await asyncio.sleep(1)
    sync_new_stripe_checkout_sessions()
    await asyncio.sleep(1)
    sync_payments()


async def run_loop_tasks():
    while True:
        try:
            update_meals_table()
            await sync_google_sheet_and_local_db()

        except Exception as e:
            print(e)

        await asyncio.sleep(5)


app.register_lifespan_task(run_loop_tasks)
